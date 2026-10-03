import os
import sqlite3
import time
import threading
from flask import g, current_app

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

CREATE TABLE IF NOT EXISTS hits (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts      INTEGER NOT NULL,
    site    TEXT NOT NULL,
    path    TEXT NOT NULL,
    ref     TEXT,
    ua      TEXT,
    lang    TEXT,
    w       INTEGER,
    session TEXT,
    country TEXT,
    bot     INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          INTEGER NOT NULL,
    site        TEXT NOT NULL,
    session     TEXT,
    path        TEXT,
    name        TEXT NOT NULL,
    props       TEXT,
    ua          TEXT,
    country     TEXT,
    bot         INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_site_ts      ON hits(site, ts);
CREATE INDEX IF NOT EXISTS idx_site_session ON hits(site, session);
CREATE INDEX IF NOT EXISTS idx_events_site_ts  ON events(site, ts);
CREATE INDEX IF NOT EXISTS idx_events_session ON events(site, session);
CREATE INDEX IF NOT EXISTS idx_events_name    ON events(name);
"""


def get_db():
    """Return a per-request SQLite connection stored on Flask's g object."""
    if "_db" not in g:
        g._db = sqlite3.connect(
            current_app.config["DB_PATH"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g._db.row_factory = sqlite3.Row
    return g._db


def close_db(e=None):
    db = g.pop("_db", None)
    if db is not None:
        db.close()


def init_db(app):
    """Called once at startup to create schema if not present."""
    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA)
        # Non-destructive migrations
        for stmt in (
            "ALTER TABLE hits ADD COLUMN country TEXT",
            "ALTER TABLE hits ADD COLUMN bot INTEGER DEFAULT 0",
        ):
            try:
                db.execute(stmt)
                db.commit()
            except Exception:
                pass  # column already exists
        # Start data retention background job if enabled
        maybe_start_retention_job(app)


# ──────────────────────────────────────────────────────────────────────────────
# Data Retention / Archiving
# ──────────────────────────────────────────────────────────────────────────────

# Configurable via env vars:
# RETENTION_DAYS       - days to keep raw hits/events (default: 365)
# RETENTION_BATCH_SIZE - rows per delete batch (default: 10000)
# RETENTION_INTERVAL   - hours between cleanup runs (default: 24)
# RETENTION_ENABLED    - set to 'false' to disable (default: true)
# RETENTION_ARCHIVE    - set to 'true' to archive instead of delete (default: false)

_retention_thread: threading.Thread | None = None
_retention_stop = threading.Event()


def _retention_config() -> dict:
    """Read retention configuration from environment."""
    return {
        "days": int(os.environ.get("RETENTION_DAYS", "365")),
        "batch_size": int(os.environ.get("RETENTION_BATCH_SIZE", "10000")),
        "interval_hours": int(os.environ.get("RETENTION_INTERVAL", "24")),
        "enabled": os.environ.get("RETENTION_ENABLED", "true").lower() != "false",
        "archive": os.environ.get("RETENTION_ARCHIVE", "false").lower() == "true",
    }


def _retention_loop(app, config):
    """Background loop that periodically deletes/archives old data."""
    with app.app_context():
        while not _retention_stop.wait(config["interval_hours"] * 3600):
            try:
                _run_retention(app, config)
            except Exception as e:
                current_app.logger.error(f"Data retention job failed: {e}")


def _run_retention(app, config):
    """Execute one retention pass: delete/archive hits and events older than retention_days."""
    cutoff = int(time.time()) - config["days"] * 86400
    batch_size = config["batch_size"]
    
    with app.app_context():
        db = get_db()
        
        # Count rows to be affected (for logging)
        hits_count = db.execute(
            "SELECT COUNT(*) FROM hits WHERE ts < ? AND (bot IS NULL OR bot = 0)",
            [cutoff]
        ).fetchone()[0]
        
        events_count = db.execute(
            "SELECT COUNT(*) FROM events WHERE ts < ? AND (bot IS NULL OR bot = 0)",
            [cutoff]
        ).fetchone()[0]
        
        if hits_count == 0 and events_count == 0:
            current_app.logger.info("Data retention: no rows to clean")
            return
        
        if config["archive"]:
            # Archive mode: move to archive tables (future enhancement)
            # For now, just log and skip actual archiving to avoid schema changes
            current_app.logger.info(
                f"Data retention: archive mode enabled but not implemented; "
                f"would archive {hits_count} hits and {events_count} events older than {config['days']} days"
            )
            return
        
        # Delete in batches to avoid locking the DB for too long
        total_deleted_hits = 0
        total_deleted_events = 0
        
        while True:
            # Delete hits batch
            result = db.execute(
                "DELETE FROM hits WHERE id IN ("
                "    SELECT id FROM hits WHERE ts < ? AND (bot IS NULL OR bot = 0) LIMIT ?"
                ")",
                [cutoff, batch_size]
            )
            deleted = result.rowcount
            total_deleted_hits += deleted
            db.commit()
            
            if deleted < batch_size:
                break
        
        while True:
            # Delete events batch
            result = db.execute(
                "DELETE FROM events WHERE id IN ("
                "    SELECT id FROM events WHERE ts < ? AND (bot IS NULL OR bot = 0) LIMIT ?"
                ")",
                [cutoff, batch_size]
            )
            deleted = result.rowcount
            total_deleted_events += deleted
            db.commit()
            
            if deleted < batch_size:
                break
        
        # VACUUM to reclaim space (run after all batches)
        try:
            db.execute("VACUUM")
            db.commit()
        except Exception:
            pass  # VACUUM may fail if DB locked, not critical
        
        current_app.logger.info(
            f"Data retention: deleted {total_deleted_hits} hits and "
            f"{total_deleted_events} events older than {config['days']} days"
        )


def maybe_start_retention_job(app):
    """Start the background retention thread if enabled and not already running."""
    global _retention_thread, _retention_stop
    
    config = _retention_config()
    if not config["enabled"]:
        return
    
    if _retention_thread is not None and _retention_thread.is_alive():
        return
    
    _retention_stop.clear()
    _retention_thread = threading.Thread(
        target=_retention_loop,
        args=(app, config),
        daemon=True,
        name="nanoanalytics-retention",
    )
    _retention_thread.start()
    current_app.logger.info(
        f"Data retention job started: every {config['interval_hours']}h, "
        f"keep {config['days']} days, batch={config['batch_size']}"
    )


def stop_retention_job():
    """Stop the background retention thread (for testing/graceful shutdown)."""
    global _retention_thread, _retention_stop
    if _retention_thread is not None:
        _retention_stop.set()
        _retention_thread.join(timeout=5)
        _retention_thread = None


def trigger_retention_now(app):
    """Manually trigger a retention pass (for API endpoint / testing)."""
    config = _retention_config()
    _run_retention(app, config)


def get_retention_status() -> dict:
    """Get current retention configuration and status."""
    config = _retention_config()
    cutoff = int(time.time()) - config["days"] * 86400
    
    hits_old = 0
    events_old = 0
    
    # Execute queries inside app context to avoid closed connection
    from flask import current_app
    try:
        with current_app.app_context():
            db = get_db()
            hits_old = db.execute(
                "SELECT COUNT(*) FROM hits WHERE ts < ? AND (bot IS NULL OR bot = 0)",
                [cutoff]
            ).fetchone()[0]
            events_old = db.execute(
                "SELECT COUNT(*) FROM events WHERE ts < ? AND (bot IS NULL OR bot = 0)",
                [cutoff]
            ).fetchone()[0]
    except RuntimeError:
        pass
    
    return {
        "enabled": config["enabled"],
        "retention_days": config["days"],
        "batch_size": config["batch_size"],
        "interval_hours": config["interval_hours"],
        "archive_mode": config["archive"],
        "cutoff_timestamp": cutoff,
        "hits_eligible_for_cleanup": hits_old,
        "events_eligible_for_cleanup": events_old,
        "thread_alive": _retention_thread is not None and _retention_thread.is_alive(),
    }