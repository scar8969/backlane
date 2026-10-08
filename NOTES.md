== curl ==
# POST /api/routes  {"host":"app.me","path":"/","upstream":"http://127.0.0.1:8000","auth":"required","rate":100}
# GET  /api/routes
# GET  /api/logs?q=/users
# GET  /api/logs/stream   (SSE)
# GET  /api/logs/export   (CSV)
# GET  /app.me/anything   (proxied — set Host header)
# CLI: rlpa route add app.me http://127.0.0.1:8000 --auth required --rate 100

== session plan ==
# Session 1: router + forward (mock upstream) → tests
# Session 2: auth + rate limit → tests
# Session 3: logs + SSE + web templates + cli → screenshots → README → CI/Docker/Pages → tag
