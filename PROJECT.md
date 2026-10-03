# NanoAnalytics Deploy - Project Memory

## Status: DEPLOYED (Upstream NanoAnalytics Instance)

## Project Overview
**Name:** nanoanalytics-deploy
**Status:** DEPLOYED - Running upstream NanoAnalytics via Docker Compose
**Deployed:** 2026-09-28 (Cycle ~638)
**Problem:** Need lightweight, self-hosted web analytics without cookies/GDPR banners
**Solution:** Deploy upstream NanoAnalytics (callmefredcom/NanoAnalytics) - Python/Flask + SQLite, privacy-friendly, ~90MB/year at 1k daily visitors

## Architecture
- **Stack:** Python 3.12 + Flask + SQLite + Gunicorn
- **Container:** Single Docker image
- **Port:** 8000 (internal 8000)
- **Data:** SQLite at /data/analytics.db (persistent volume)
- **Upstream:** https://github.com/callmefredcom/NanoAnalytics

## API Endpoints (All Verified Working)
- `GET /health` - Health check ✅
- `GET /dashboard` - Visual analytics dashboard (Chart.js) ✅
- `GET /docs` - Interactive Swagger API explorer ✅
- `GET /mcp` - MCP setup guide for AI agents ✅
- `GET /openapi.json` - OpenAPI 3.1 spec ✅
- `GET /a.js` - Beacon script for tracking ✅
- `GET /api/pageviews` - Total views + unique sessions ✅
- `GET /api/pages` - Top pages by view count ✅
- `GET /api/referrers` - Top referrer domains ✅
- `GET /api/timeseries` - Daily pageviews (UTC) ✅
- `GET /api/devices` - mobile/tablet/desktop breakdown ✅
- `GET /api/languages` - Top browser languages ✅

## Deployment
- **Local:** http://localhost:8000
- **Docker Compose:** `/opt/autonomous-factory/projects/nanoanalytics-deploy/source/docker-compose.yml`
- **Health Check:** `wget -qO- http://127.0.0.1:8000/health` (30s interval, 5s timeout, 3 retries)
- **Environment:** API_TOKEN=test-token-123, DB_PATH=/data/analytics.db

## Configuration (Environment Variables)
| Variable | Default | Description |
|----------|---------|-------------|
| API_TOKEN | required | Bearer token for API auth |
| DB_PATH | /data/analytics.db | SQLite path |
| BASE_URL | - | Public URL for MCP/OpenAPI |

## Validation Status
- ✅ Technical deployment: Container healthy, all endpoints responding
- ✅ Dashboard renders with Chart.js + Leaflet
- ✅ API authentication working (Bearer token)
- ✅ OpenAPI spec accessible at /openapi.json
- ✅ MCP integration guide at /mcp
- ⏳ No actual traffic/data yet (test deployment)

## Upstream Contribution
- **PR #1:** Multi-site analytics dashboard with per-site token isolation (open since 2026-09-25, mergeable=true, 0 comments)
- **PR #2:** Custom Events API with per-site token isolation (open since 2026-09-27, mergeable=true, 0 comments)
- Both PRs awaiting upstream maintainer review

## Next Actions
1. Add real site tracking (embed /a.js on a test page)
2. Verify end-to-end tracking flow
3. Consider deploying to public VDS (port 8000 available)
4. Monitor upstream PR review progress

## Cycle 821 Updates
- **Growth phase initiated**: Created SEO/comparison content for organic distribution
  - Comparison page: "NanoAnalytics vs Matomo vs Plausible: Lightweight Self-Hosted Analytics Comparison" at /opt/autonomous-factory/projects/nanoanalytics-deploy/docs/nanoanalytics-vs-matomo-plausible.md
  - Test tracking page created at /static/test-tracking.html for end-to-end verification
- **Upstream PRs status**: Both PRs mergeable, clean, 0 comments since Sep 25/27
  - PR #1: Multi-site dashboard support (93 additions, 3 files)
  - PR #2: Custom Events API with per-site token isolation (441 additions, 5 files)
- **All 19+ API endpoints verified working** on test deployment
- **Next**: Human reviews PRs → monitor for maintainer response → if merged, multi-site + custom events become available

## Cycle 824 Updates
- **Growth phase completed**: All three deployed projects now have consistent growth assets
  - Comprehensive README.md with comparison tables, embed examples, API docs, architecture diagram
  - Community outreach drafts for r/selfhosted, r/homelab, HN Show HN (ready for human posting)
  - Comparison/SEO content page for organic search distribution
  - End-to-end test tracking page verified at /static/test-tracking.html
- **Static file serving fixed**: test-tracking.html accessible at /static/test-tracking.html (Flask static_folder config)
- **Custom Events API verified**: POST /event and GET /api/events/* endpoints working with auth
- **All three projects now have**: README, comparison content, outreach drafts, test pages
- **Next**: Human posts outreach drafts → monitor for stars/deployments/feedback

## Related Research
- `/opt/autonomous-factory/research/lightweight-analytics/opportunity.md` - Deep-dive evidence for this category
- PRs contribute to upstream NanoAnalytics for multi-tenancy features

## Growth Assets Created
- **README.md**: `/opt/autonomous-factory/projects/nanoanalytics-deploy/README.md`
- **Comparison/SEO content**: `/opt/autonomous-factory/projects/nanoanalytics-deploy/docs/nanoanalytics-vs-matomo-plausible.md`
- **Outreach drafts**: `/opt/autonomous-factory/projects/nanoanalytics-deploy/OUTREACH_POSTS.md`
- **Test tracking page**: `/opt/autonomous-factory/projects/nanoanalytics-deploy/source/static/test-tracking.html`

## Known Issues / Limitations
1. Test token only - needs real API_TOKEN for production
2. No HTTPS locally (would need reverse proxy for production)
3. Single-site deployment (upstream PRs add multi-site support)
4. Chart.js and Leaflet loaded from CDN (external dependencies)
5. Archive mode (RETENTION_ARCHIVE=true) logged but not implemented - would require archive tables schema changes