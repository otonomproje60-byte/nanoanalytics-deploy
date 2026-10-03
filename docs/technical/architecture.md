# NanoAnalytics - Technical Architecture

## Overview
NanoAnalytics is a lightweight, self-hosted web analytics platform. Our fork (nanoanalytics-deploy) adds multi-site dashboard and Custom Events API on top of the upstream NanoAnalytics (Flask + SQLite). Designed as a privacy-friendly, resource-efficient alternative to Matomo (21k★, heavy) and Plausible (29k★, paid cloud).

## Technology Stack
- **Language**: Python 3.11
- **Framework**: Flask (synchronous)
- **Database**: SQLite (embedded, file-based)
- **WSGI**: Gunicorn (multi-worker)
- **Container**: Docker (single container, ~50MB image, ~50MB RAM)
- **Deployment**: Docker Compose on port 8000

## Architecture Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                      Client Websites                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  <script    │  │  <img       │  │  fetch('/event',    │  │
│  │  src="/a.js"│  │  src="/hit"  │  │  {method:'POST'})   │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                    │              │
│         └────────────────┼────────────────────┘              │
│                          │ HTTP/HTTPS                          │
│                          ▼                                    │
┌─────────────────────────────────────────────────────────────┐
│                     NanoAnalytics (8000)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Flask      │  │  Jinja2      │  │   SQLite DB      │  │
│  │  Application │──│  Templates   │  │  (analytics.db)  │  │
│  └──────────────┘  └──────────────┘  └──────────────────┘  │
│        │                                    │               │
│  ┌─────▼─────┐                        ┌─────▼─────┐         │
│  │  In-Memory│                        │  GeoIP    │         │
│  │  Caches   │                        │  (offline)│         │
│  │ (per      │                        │           │         │
│  │  worker)  │                        └───────────┘         │
│  └───────────┘                                              │
└─────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Flask Application (`nano_analytics/routes.py`)
- Blueprint-based modular routes
- Public endpoints: `/hit` (beacon), `/event` (custom events), `/a.js` (tracker)
- Protected API: `/api/*` (token auth, per-site isolation)
- Admin UI: `/dashboard`, `/docs`, `/mcp`
- Comparison page: `/compare`

### 2. Database Schema
```sql
-- Hits (page views)
hits: ts, site, path, ref, ua, lang, w (screen width), session, country, bot

-- Custom Events (NEW in fork)
events: ts, site, session, path, name, props (JSON), ua, country, bot

-- Sites metadata (NEW in fork - derived from hits/events)
sites: (derived via /api/sites - distinct sites with stats)

-- Retention config
retention_config: key, value
```

### 3. Bot Detection (`_is_bot()`)
- User-Agent regex: bot/crawl/spider/slurp/HeadlessChrome/python-requests/curl/wget/axios/node-fetch/Go-http-client/Java/libwww/okhttp/Scrapy
- Chrome version check: Chrome > 109 on Windows 7 (NT 6.1) = impossible
- Flood detection: Sliding window per site (300 hits/min/worker)
- **Private IP whitelist**: Same-origin traffic (localhost, 10.x, 172.16-31.x, 192.168.x) exempted from bot detection

### 4. Response Caching (`@cache_response`)
- In-memory cache per gunicorn worker
- TTL: 1 hour for historical data (end < today), 2 min for ranges including today
- Cache invalidation on new events (`_invalidate_events_cache()`)
- Keyed by function name + query string

### 5. Multi-Site Token Isolation (`_check_site_authorization()`)
- Global token: access to all sites
- Per-site token: restricted to single site (root domain matching)
- Root domain normalization: `www.example.com` → `example.com`
- Subdomain wildcard: `%.example.com` matches all subdomains

### 6. Offline GeoIP (`geoip2fast`)
- Bundled GeoIP database, zero external calls
- Returns ISO 3166-1 alpha-2 country codes
- Private IPs return `None`

## API Endpoints

### Public (No Auth)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/hit` | Beacon endpoint (1×1 GIF), inserts hit |
| POST | `/event` | Custom events (JSON: site, name, props, session, path) |
| GET | `/a.js` | Tracking script |
| GET | `/health` `/healthz` | Health checks |
| GET | `/` `/dashboard` `/docs` `/mcp` | UI pages |
| GET | `/compare` | Comparison page |

### Protected API (Token Auth: `Authorization: Bearer <token>`)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/pageviews` | Total views + unique sessions |
| GET | `/api/pages` | Top pages |
| GET | `/api/referrers` | Top referrers (self-referrals excluded) |
| GET | `/api/timeseries` | Daily/hourly views + sessions |
| GET | `/api/browsers` | Browser breakdown |
| GET | `/api/os` | OS breakdown |
| GET | `/api/devices` | Device type breakdown |
| GET | `/api/languages` | Top languages |
| GET | `/api/countries` | Top countries |
| GET | `/api/active` | Active sessions (last N seconds) |
| GET | `/api/hostnames` | Subdomain breakdown |
| GET | `/api/entry-pages` | Top entry pages |
| GET | `/api/peak-hours` | Busiest hours (UTC) |
| GET | `/api/bounce-rates` | Bounce rate per page |
| GET | `/api/exit-pages` | Top exit pages |
| GET | `/api/screen-widths` | Screen width buckets |
| GET | `/api/session-duration` | Average session duration |
| GET | `/api/filter-values` | Autocomplete for filters |
| GET | `/api/sites` | **Multi-site dashboard** - all sites with stats |

### Custom Events API (NEW in Fork)
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/events/names` | Event names with counts |
| GET | `/api/events/stats` | Event counts by name |
| GET | `/api/events/timeseries` | Events over time (daily/hourly) |
| GET | `/api/events/funnels` | Funnel analysis (comma-separated steps) |
| GET | `/api/events/props` | Distinct property values for event+prop |

### Admin API
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/admin/retention/status` | Retention config/status |
| POST | `/api/admin/retention/run` | Trigger retention job |

## Security Considerations
- **Token isolation**: Per-site tokens cannot access other sites' data
- **Bot filtering**: Automatic detection + flood protection
- **Private IP whitelist**: Legitimate server-side requests not flagged
- **SQL injection**: Parameterized queries only
- **Rate limiting**: Flood detection per site
- **CORS**: `Access-Control-Allow-Origin: *` on `/hit` and `/a.js` for cross-origin tracking
- **No auth on dashboard**: Designed for internal/VPN use

## Deployment
```yaml
# docker-compose.yml
services:
  nanoanalytics:
    build: ./source
    ports: ["8000:8000"]
    volumes: ["./data:/data"]
    environment:
      - DATABASE_PATH=/data/analytics.db
      - BASE_URL=http://77.90.53.243:8000
      - TOKEN=***           # Global admin token
      - SITE_TOKENS=***     # Optional: JSON map of site->token
```

## Data Persistence
- SQLite database at `/data/analytics.db` (Docker volume)
- WAL mode enabled for concurrent reads/writes
- Retention: Configurable (default 90 days hits, 365 days events)
- Backup: `sqlite3 analytics.db .dump > backup.sql`

## Key Differentiators (Fork vs Upstream)
1. **Multi-site dashboard** (`/api/sites`) - Single token manages multiple sites
2. **Custom Events API** (`/event` + `/api/events/*`) - Track conversions, funnels, button clicks
3. **Per-site token isolation** - Granular access control
4. **Private IP whitelist** - Server-side rendering not flagged as bot
5. **Event funnel analysis** - Multi-step conversion tracking
6. **Property value extraction** - Drill into event properties

## File Structure
```
source/
├── docker-compose.yml
├── Dockerfile
├── Dockerfile (updated with COPY docs/)
├── README.md
├── pyproject.toml
├── gunicorn.conf.py
├── wsgi.py
├── nano_analytics/
│   ├── __init__.py
│   ├── routes.py          # All routes (450+ lines)
│   ├── db.py              # DB connection, retention
│   ├── auth.py            # Token auth, site authorization
│   ├── ua_parser.py       # Browser/OS/device parsing
│   ├── openapi.py         # OpenAPI spec
│   └── bots/              # Bot definitions
├── static/
│   └── a.js               # Tracking beacon
├── templates/
│   ├── dashboard.html
│   ├── docs.html
│   ├── mcp.html
│   └── compare.html
└── docs/
    ├── nanoanalytics-vs-matomo-plausible.md
    └── technical/
        └── architecture.md
```

## Testing
```bash
# Health check
curl http://localhost:8000/health

# Beacon test
curl "http://localhost:8000/hit?site=example.com&path=/test"

# Custom event test
curl -X POST http://localhost:8000/event \
  -H "Content-Type: application/json" \
  -d '{"site":"example.com","name":"button_click","props":{"id":"cta"}}'

# API test (with token)
curl -H "Authorization: Bearer your-token" \
  "http://localhost:8000/api/pageviews?site=example.com"

# Multi-site dashboard
curl -H "Authorization: Bearer your-token" \
  "http://localhost:8000/api/sites"
```

## Monitoring
- Health endpoints: `/health`, `/healthz` (both return `{"status": "ok"}`)
- Logs: `docker logs source_web_1`
- Metrics: All analytics via protected API

## Future Enhancements (Post-Validation)
- Real-time dashboard (WebSocket)
- Cohort analysis
- A/B testing framework
- Export to CSV/Parquet
- Grafana datasource plugin
- Alerting on traffic anomalies