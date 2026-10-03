# NanoAnalytics

Lightweight, self-hosted web analytics. No cookies. No GDPR banners. < 400 byte beacon.

```
┌─────────────────────────────────────────────────────────────┐
│  NanoAnalytics - Privacy-first web analytics                │
│  Python/Flask + SQLite  |  ~90MB/year at 1K daily visitors  │
│  MIT License          |  Single container deployment        │
└─────────────────────────────────────────────────────────────┘
```

## Why NanoAnalytics?

| Feature | **NanoAnalytics** | Matomo | Plausible | Google Analytics |
|---------|-------------------|--------|-----------|------------------|
| **RAM** | ~20MB | ~200-500MB | ~100-200MB | N/A (SaaS) |
| **Services** | 1 container | 3+ (PHP, MySQL, Redis) | 2+ (Elixir, ClickHouse) | N/A |
| **Cookies** | **None** | Yes (opt-out) | **None** | Yes |
| **GDPR Banner** | **Not needed** | Required | **Not needed** | Required |
| **Self-hosted** | ✅ Single `docker up` | Complex | Medium | ❌ SaaS only |
| **License** | MIT | GPL-3.0 | AGPL-3.0 | Proprietary |
| **Custom Events** | ✅ Built-in | ✅ | ✅ | ✅ |
| **Multi-site** | ✅ (PR #1 open) | ✅ | ✅ | ✅ |
| **Beacon Size** | **< 400 bytes** | ~20KB | ~1KB | ~45KB |
| **Price** | **Free** | Free/Cloud €19+/mo | Cloud $9+/mo | Free/Enterprise |

## Quick Start

```bash
# Clone and deploy
git clone https://github.com/otonomproje60-byte/nanoanalytics-deploy.git
cd nanoanalytics-deploy
docker compose up -d

# Visit http://localhost:8000
# Dashboard: http://localhost:8000/dashboard
# API Docs: http://localhost:8000/docs
# OpenAPI: http://localhost:8000/openapi.json
```

## Embedding on Your Site

Add this before `</head>`:

```html
<script src="https://your-domain.com/a.js" data-site="your-site.example.com"></script>
```

Or manually:

```html
<script>
(function() {
  var s = document.createElement('script');
  s.src = 'https://your-domain.com/a.js';
  s.dataset.site = 'your-site.example.com';
  document.head.appendChild(s);
})();
</script>
```

**That's it.** The beacon auto-detects pageviews, sessions, referrers, devices, languages.

## Custom Events API

Track button clicks, form submissions, purchases, anything:

```javascript
// Using the beacon's global
window.nano = window.nano || [];
nano.push(['event', 'signup', { plan: 'pro', source: 'header' }]);
nano.push(['event', 'purchase', { amount: 49, currency: 'USD', items: 2 }]);
```

Or direct POST (server-side):

```bash
curl -X POST https://your-domain.com/event \
  -H "Content-Type: application/json" \
  -d '{
    "site": "your-site.example.com",
    "name": "signup",
    "props": { "plan": "pro", "source": "header" },
    "session": "abc123",
    "path": "/pricing"
  }'
```

**Server response:** `{"status":"ok"}`

### Query Custom Events

```bash
# List event names
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://your-domain.com/api/events/names?site=your-site.example.com"

# Get stats for an event
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://your-domain.com/api/events/stats?site=your-site.example.com&name=signup"

# Time series
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://your-domain.com/api/events/timeseries?site=your-site.example.com&name=signup&days=30"

# Property breakdown
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://your-domain.com/api/events/props?site=your-site.example.com&name=signup&prop=plan"

# Funnels
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "https://your-domain.com/api/events/funnel?site=your-site.example.com&steps=signup,purchase"
```

## API Endpoints

All endpoints require `Authorization: Bearer YOUR_TOKEN` except `/hit`, `/a.js`, `/health`, `/docs`, `/mcp`, `/openapi.json`.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/dashboard` | GET | Visual dashboard (Chart.js + Leaflet) |
| `/docs` | GET | Swagger UI |
| `/mcp` | GET | MCP integration guide |
| `/openapi.json` | GET | OpenAPI 3.1 spec |
| `/a.js` | GET | Tracking beacon (< 400 bytes) |
| `/hit` | GET | Pageview beacon (query params: `site`, `path`) |
| `/event` | POST | Custom event ingestion |
| `/api/pageviews` | GET | Total views + unique sessions |
| `/api/pages` | GET | Top pages by view count |
| `/api/referrers` | GET | Top referrer domains |
| `/api/timeseries` | GET | Daily pageviews (UTC) |
| `/api/devices` | GET | mobile/tablet/desktop breakdown |
| `/api/languages` | GET | Top browser languages |
| `/api/events/names` | GET | List custom event names |
| `/api/events/stats` | GET | Event counts + unique sessions |
| `/api/events/timeseries` | GET | Daily event counts |
| `/api/events/props` | GET | Property value breakdown |
| `/api/events/funnel` | GET | Multi-step funnel conversion |

### API Query Parameters

| Parameter | Endpoints | Description |
|-----------|-----------|-------------|
| `site` | All `/api/*` | Site identifier (required) |
| `days` | timeseries | Days of history (default: 30) |
| `name` | events/stats, timeseries, props, funnel | Event name |
| `prop` | events/props | Property key to break down |
| `steps` | events/funnel | Comma-separated funnel steps |

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Your Site     │────▶│  /a.js beacon    │────▶│  /hit endpoint  │
│  (visitor)      │     │  (< 400 bytes)   │     │  (pageview)     │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                    ┌──────────────────┐                  │
                    │  /event endpoint │◀─────────────────┘
                    │ (custom events)  │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  SQLite Database │
                    │  /data/analytics.db
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌───────────┐ ┌─────────────┐ ┌─────────────┐
        │ /dashboard│ │  /api/*     │ │  /docs      │
        │ (Chart.js │ │  (JSON)     │ │  (Swagger)  │
        │ + Leaflet)│ │             │ │             │
        └───────────┘ └─────────────┘ └─────────────┘
```

## Configuration

Environment variables (set in `docker-compose.yml` or `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `API_TOKEN` | required | Bearer token for API authentication |
| `DB_PATH` | `/data/analytics.db` | SQLite database path |
| `BASE_URL` | - | Public URL for MCP/OpenAPI links |

### docker-compose.yml

```yaml
services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - analytics_data:/data
    environment:
      - API_TOKEN=your-secure-token-here
      - DB_PATH=/data/analytics.db
      - BASE_URL=https://analytics.yourdomain.com
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://127.0.0.1:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3

volumes:
  analytics_data:
    driver: local
```

## Production Deployment

### Reverse Proxy (nginx)

```nginx
server {
    listen 80;
    server_name analytics.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### HTTPS (Let's Encrypt)

```bash
certbot --nginx -d analytics.yourdomain.com
```

### Systemd (if not using Docker)

```ini
[Unit]
Description=NanoAnalytics
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/nanoanalytics
Environment=API_TOKEN=your-token
Environment=DB_PATH=/var/lib/nanoanalytics/analytics.db
Environment=BASE_URL=https://analytics.yourdomain.com
ExecStart=/opt/nanoanalytics/.venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 wsgi:app
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

## Upstream Contributions

This deployment includes two open PRs to upstream NanoAnalytics:

- **PR #1**: [Multi-site analytics dashboard with per-site token isolation](https://github.com/callmefredcom/NanoAnalytics/pull/1) - 93 additions, 3 files, mergeable since 2026-09-25
- **PR #2**: [Custom Events API with per-site token isolation](https://github.com/callmefredcom/NanoAnalytics/pull/2) - 441 additions, 5 files, mergeable since 2026-09-27

Both await maintainer review. Once merged, multi-site + custom events become native upstream features.

## Test Page

Verify your deployment end-to-end:

```
https://your-domain.com/static/test-tracking.html
```

This page tests:
- Pageview tracking (`/hit`)
- Custom events (`/event` with various props)
- API data retrieval
- Beacon loading verification

## Project Structure

```
nanoanalytics-deploy/
├── source/
│   ├── nano_analytics/
│   │   ├── __init__.py      # Flask app factory
│   │   ├── routes.py        # All API endpoints
│   │   ├── db.py            # SQLite operations
│   │   └── templates/       # Dashboard HTML
│   ├── static/
│   │   ├── a.js             # Beacon script
│   │   └── test-tracking.html  # End-to-end test page
│   ├── wsgi.py              # Gunicorn entry point
│   └── docker-compose.yml
├── docs/
│   └── nanoanalytics-vs-matomo-plausible.md  # Comparison/SEO content
├── PROJECT.md               # Project memory
└── README.md                # This file
```

## Development

```bash
# Local development
cd source
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export API_TOKEN=dev-token
export DB_PATH=/tmp/analytics.db
flask --app nano_analytics:create_app run --debug

# Run tests
pytest tests/
```

## Monitoring

```bash
# Health check
curl https://analytics.yourdomain.com/health

# Container logs
docker logs -f nanoanalytics

# Database size
docker exec nanoanalytics ls -lh /data/analytics.db
```

## Privacy & Compliance

- **No cookies** - Uses `sessionStorage` only (cleared on tab close)
- **No personal data** - No IP storage, no fingerprinting
- **GDPR compliant by design** - No consent banner needed
- **Data ownership** - Your server, your data, your SQLite file
- **Open source** - MIT license, audit the code

## Roadmap

- [ ] Upstream PR #1 merged (multi-site dashboard)
- [ ] Upstream PR #2 merged (custom events API)
- [ ] Data retention policies (auto-archive old data)
- [ ] Export/import (JSON, CSV)
- [ ] Webhook notifications for anomalies
- [ ] Team/multi-user support
- [ ] Prometheus metrics endpoint

## Comparison: NanoAnalytics vs Alternatives

See [docs/nanoanalytics-vs-matomo-plausible.md](docs/nanoanalytics-vs-matomo-plausible.md) for a detailed comparison covering:
- Resource usage benchmarks
- Feature parity matrix
- Deployment complexity
- License implications
- Total cost of ownership

## License

MIT License - see [LICENSE](LICENSE) for details.

Upstream NanoAnalytics: https://github.com/callmefredcom/NanoAnalytics (MIT)

---

**Built for homelabbers, developers, and privacy advocates who want analytics without the bloat.**

*Deploy it. Own it. Forget it.*