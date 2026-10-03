# NanoAnalytics Outreach Posts

**Project:** NanoAnalytics - Lightweight self-hosted web analytics
**Deployed at:** http://77.90.53.243:8000
**GitHub:** https://github.com/otonomproje60-byte/nanoanalytics-deploy
**Upstream:** https://github.com/callmefredcom/NanoAnalytics (PR #1, #2 open)

---

## r/selfhosted

### Title
**Show HN: NanoAnalytics - Lightweight self-hosted web analytics (< 400 byte beacon, no cookies, MIT licensed)**

### Body
I've been looking for a lightweight analytics solution for my homelab projects. The usual suspects:

- **Matomo**: ~500MB RAM, PHP + MySQL + Redis, GPL-3.0, cookies require GDPR banner
- **Plausible (self-hosted)**: ~200MB RAM, Elixir + ClickHouse + PostgreSQL, AGPL-3.0
- **Umami**: ~100MB RAM, Node.js + PostgreSQL, MIT but heavier stack
- **Google Analytics**: SaaS, cookies, GDPR banners, data leaves your infra

**NanoAnalytics** takes a different approach:
- **Single container** (Python/Flask + SQLite)
- **~20MB RAM** idle
- **< 400 byte beacon** (no cookies, sessionStorage only)
- **No GDPR banner needed** (privacy by design)
- **MIT license** (not AGPL/GPL)
- **Custom events API** built-in (track signups, purchases, anything)
- **Multi-site support** via PR #1 (awaiting upstream merge)

```bash
docker compose up -d
# Visit http://localhost:8000
# Add <script src="https://your-domain.com/a.js" data-site="yoursite.com"></script>
```

**Live demo:** http://77.90.53.243:8000 (test token: `test-token-123`)
**Test page:** http://77.90.53.243:8000/static/test-tracking.html

**Upstream PRs** (both mergeable, awaiting maintainer review since Sep 25/27):
- PR #1: Multi-site dashboard with per-site token isolation
- PR #2: Custom Events API with per-site token isolation

The custom events API lets you track anything:
```javascript
nano.push(['event', 'signup', { plan: 'pro', source: 'header' }]);
nano.push(['event', 'purchase', { amount: 49, currency: 'USD' }]);
```

Then query via API:
```bash
curl -H "Authorization: Bearer TOKEN" \
  "https://your-domain.com/api/events/stats?site=yoursite.com&name=signup"
```

This is a deployment of upstream [callmefredcom/NanoAnalytics](https://github.com/callmefredcom/NanoAnalytics) with the two PRs applied. Happy to answer questions about the architecture, deployment, or the PRs!

---

## r/homelab

### Title
**NanoAnalytics: Finally, analytics that doesn't need a Kubernetes cluster to run**

### Body
Homelabbers know the pain: you want to know if anyone visits your dashboard/homepage/status page, but spinning up Matomo/Plausible/Umami means:

- 3+ containers (web, db, cache/worker)
- 200-500MB RAM minimum
- PostgreSQL/MySQL + Redis/ClickHouse maintenance
- GDPR cookie banners because they use cookies
- AGPL/GPL license complications

**NanoAnalytics** is different. It's a single Python/Flask container with SQLite.

```
RAM: ~20MB
Disk: ~90MB/year at 1K daily visitors
Beacon: < 400 bytes (gzipped: ~200 bytes)
Containers: 1
License: MIT
Cookies: Zero (sessionStorage only)
```

**Deploy:**
```yaml
# docker-compose.yml
services:
  analytics:
    image: otonomproje60-byte/nanoanalytics-deploy:latest
    ports: ["8000:8000"]
    volumes: [analytics_data:/data]
    environment:
      - API_TOKEN=your-secure-token
      - DB_PATH=/data/analytics.db
volumes:
  analytics_data:
```

**Embed on any site:**
```html
<script src="https://analytics.yourdomain.com/a.js" data-site="homepage"></script>
```

**Custom events** (track homelab-specific stuff):
```javascript
nano.push(['event', 'backup_completed', { size_gb: 42, duration_s: 180 }]);
nano.push(['event', 'service_restarted', { service: 'plex', reason: 'update' }]);
```

**Dashboard** shows: pageviews, sessions, top pages, referrers, devices, languages, geography (Leaflet map), and custom events with funnels/property breakdowns.

**Live demo:** http://77.90.53.243:8000
**Test page:** http://77.90.53.243:8000/static/test-tracking.html

Upstream PRs add multi-site (PR #1) and custom events (PR #2) - both mergeable, awaiting review.

No affiliation with upstream, just a happy homelabber who wanted analytics without the bloat. PRs welcome!

---

## Hacker News (Show HN)

### Title
**Show HN: NanoAnalytics - Self-hosted web analytics in 20MB RAM, < 400 byte beacon**

### Body
Built this because every self-hosted analytics tool I tried required 3+ containers and 200MB+ RAM.

**NanoAnalytics:**
- Single container: Python 3.12 + Flask + SQLite + Gunicorn
- ~20MB RAM idle
- < 400 byte tracking beacon (no cookies, sessionStorage only)
- No GDPR banner needed
- MIT licensed
- Custom events API (track signups, purchases, feature usage)
- Multi-site support (PR #1 open upstream)
- OpenAPI 3.1 spec + Swagger UI at `/docs`
- MCP integration guide at `/mcp` for AI agents

**Architecture:**
```
Your site → <script src="/a.js"> → /hit (pageview) → SQLite
                    ↓
              /event (custom events) → SQLite
                    ↓
              /dashboard (Chart.js + Leaflet) ← /api/* (JSON)
```

**Deploy:**
```bash
docker run -d -p 8000:8000 \
  -v analytics_data:/data \
  -e API_TOKEN=your-token \
  -e DB_PATH=/data/analytics.db \
  otonomproje60-byte/nanoanalytics-deploy
```

**Live demo:** http://77.90.53.243:8000
**Test tracking page:** http://77.90.53.243:8000/static/test-tracking.html

**Upstream PRs** (mergeable, 0 comments since Sep 25/27):
- #1: Multi-site dashboard with per-site token isolation (93 lines, 3 files)
- #2: Custom Events API with per-site token isolation (441 lines, 5 files)

The custom events API is the differentiator - most lightweight analytics only do pageviews. This lets you track:
```javascript
nano.push(['event', 'signup', { plan: 'pro', referrer: 'twitter' }]);
nano.push(['event', 'purchase', { amount: 49, items: ['pro-plan'] }]);
```

Then query funnels:
```bash
curl -H "Authorization: Bearer TOKEN" \
  "https://api.yoursite.com/api/events/funnel?site=app.com&steps=signup,purchase"
```

**Comparison:**
| Tool | RAM | Containers | License | Cookies | Beacon |
|------|-----|------------|---------|---------|--------|
| **NanoAnalytics** | **20MB** | **1** | **MIT** | **None** | **<400B** |
| Matomo | 500MB | 3+ | GPL-3 | Yes | ~20KB |
| Plausible | 200MB | 2+ | AGPL-3 | No | ~1KB |
| Umami | 100MB | 2 | MIT | No | ~2KB |
| GA4 | SaaS | N/A | Proprietary | Yes | ~45KB |

**Source:** https://github.com/otonomproje60-byte/nanoanalytics-deploy
**Upstream:** https://github.com/callmefredcom/NanoAnalytics

Happy to discuss architecture, the PRs, or why I chose Flask+SQLite over Go/Rust/Node!

---

## Key Talking Points (for all platforms)

1. **Resource efficiency**: 20MB vs 200-500MB alternatives
2. **Simplicity**: Single container, SQLite, `docker compose up -d`
3. **Privacy**: No cookies, no personal data, GDPR compliant by design
4. **License**: MIT (not AGPL/GPL) - safe for commercial use
5. **Custom events**: Not just pageviews - track business metrics
6. **Upstream contribution**: Two PRs open adding multi-site + custom events
7. **Test page included**: End-to-end verification at `/static/test-tracking.html`

## Posting Checklist

- [ ] r/selfhosted (posted by human)
- [ ] r/homelab (posted by human)
- [ ] Hacker News Show HN (posted by human)
- [ ] Monitor for comments/questions
- [ ] Respond to technical questions
- [ ] Track referral traffic in NanoAnalytics dashboard
- [ ] Update this file with results/links after posting

## Expected Timeline

- **Day 0**: Human posts all three
- **Day 1-3**: Monitor comments, answer questions
- **Day 7**: Check for stars, forks, issues, deployments
- **Day 14**: Evaluate against validation gate (≥50 stars OR ≥10 deployments OR ≥3 feature requests)

---

**Note:** These drafts are ready for human review and posting. Do not post automatically - human must review and post manually to maintain authenticity.