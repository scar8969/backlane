<p align="center">
  <img src="docs/assets/screens/root.png" alt="backlane running" width="900">
</p>

<h1 align="center">backlane</h1>

<p align="center"><b>A reverse proxy with per-route auth and a log you can stream.</b></p>

<p align="center">
  <a href="https://github.com/scar8969/backlane/actions/workflows/ci.yml"><img src="https://github.com/scar8969/backlane/actions/workflows/ci.yml/badge.svg" alt="ci"></a> <a href="#quality-gates"><img src="https://img.shields.io/badge/tests-23%20passed-2ea44f" alt="tests: 23 passed"></a> <a href="#quality-gates"><img src="https://img.shields.io/badge/coverage-68.1%-yellow" alt="coverage: 68.1%"></a> <a href="#api"><img src="https://img.shields.io/badge/routes-12%20live-0969da" alt="routes: 12 live"></a> <a href="#requirements"><img src="https://img.shields.io/badge/python-3.11%2B-3776ab" alt="python: 3.11+"></a> <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2ea44f" alt="license: MIT"></a>
</p>

backlane terminates HTTP, authenticates the caller, forwards to an upstream and records the exchange. Routes are rows: host, path prefix, upstream, auth requirement. Access logs are queryable as JSON, streamable as SSE and exportable as CSV.

---

**Contents** &nbsp;·&nbsp; [Why](#why-this-exists) &nbsp;·&nbsp; [What it does](#what-it-does) &nbsp;·&nbsp; [Quickstart](#quickstart) &nbsp;·&nbsp; [Screenshots](#screenshots) &nbsp;·&nbsp; [API](#api) &nbsp;·&nbsp; [CLI](#cli) &nbsp;·&nbsp; [Configuration](#configuration) &nbsp;·&nbsp; [Measured](#measured-not-estimated) &nbsp;·&nbsp; [How a request flows](#how-a-request-flows) &nbsp;·&nbsp; [Architecture](#architecture) &nbsp;·&nbsp; [Quality gates](#quality-gates) &nbsp;·&nbsp; [Development](#development) &nbsp;·&nbsp; [Deploy](#deploy) &nbsp;·&nbsp; [Limits](#limits-stated-rather-than-hidden)

## Why this exists

nginx does this in configuration files that only one person understands and cannot query. Making routes data means adding a backend is an API call, and making the log queryable means an incident review is a filter rather than a grep over rotated files.

## What it does

| Capability | How it works |
| --- | --- |
| **Data-driven routes** | Add, list and delete routes at runtime; the catch-all resolves host and path against the table. |
| **Per-route auth** | A route can require a token; unauthorised requests are logged and refused before the upstream is touched. |
| **Access log as data** | Structured rows with status, latency and upstream, plus CSV export for a spreadsheet. |
| **Live log stream** | GET /api/logs/stream pushes new entries as SSE, so a dashboard does not poll. |

## Quickstart

```sh
git clone https://github.com/scar8969/backlane.git
cd backlane
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python wsgi.py                                 # http://127.0.0.1:8000
```

It is up when this answers:

```sh
curl -s http://127.0.0.1:8000/api/routes
```

## Screenshots

Captured from the running service with headless Chromium at 1440×900, one image per page, committed under [`docs/assets/screens/`](docs/assets/screens/).

<table>
<tr>
<td width="50%"><img src="docs/assets/screens/logs.png" alt="/logs" width="100%"><br><sub><code>/logs</code> &middot; 26.2 KB</sub></td>
<td width="50%"><img src="docs/assets/screens/healthz.png" alt="/healthz" width="100%"><br><sub><code>/healthz</code> &middot; 8.2 KB</sub></td>
</tr>
</table>

<table>
<tr>
<td width="50%"><img src="docs/assets/screens/livez.png" alt="/livez" width="100%"><br><sub><code>/livez</code> &middot; 7.3 KB</sub></td>
<td width="50%"><img src="docs/assets/screens/metrics.png" alt="/metrics" width="100%"><br><sub><code>/metrics</code> &middot; 14.9 KB</sub></td>
</tr>
</table>

<table>
<tr>
<td width="50%"><img src="docs/assets/screens/readyz.png" alt="/readyz" width="100%"><br><sub><code>/readyz</code> &middot; 7.7 KB</sub></td>
<td width="50%"><img src="docs/assets/screens/version.png" alt="/version" width="100%"><br><sub><code>/version</code> &middot; 25.6 KB</sub></td>
</tr>
</table>

## API

Every route below is declared in [`openapi/backlane.yaml`](openapi/backlane.yaml) and exercised by the live probe recorded in [`docs/EVIDENCE.md`](docs/EVIDENCE.md).

| Method | Path | What it does |
| --- | --- | --- |
| `GET` | `/api/routes` | list |
| `POST` | `/api/routes` | add route |
| `DELETE` | `/api/routes/<id>` | delete |
| `GET` | `/api/logs` | logs |
| `GET` | `/api/logs/stream` | SSE |
| `GET` | `/api/logs/export` | CSV |

## CLI

The same operations without an HTTP client. Installed as `backlane`, and runnable from a checkout with no install:

```sh
python -m rlpa_server.cli --help
```

```text
usage: rlpa [-h] {route} ...

positional arguments:
  {route}

options:
  -h, --help  show this help message and exit
```

## Configuration

Environment only — there is no config file. Copy `.env.example` to `.env` and edit; `APP_ENV=production` refuses to start without `SECRET_KEY`.

| Variable | Default | Meaning |
| --- | --- | --- |
| `APP_ENV` | `development` | development \| staging \| production; production enforces the secret. |
| `SECRET_KEY` | `change-me-in-production` | Session/CSRF signing key. Required when APP_ENV=production. |
| `HOST` | `0.0.0.0` | Interface the dev server binds. |
| `PORT` | `8000` | Port the dev server and the container listen on. |
| `DEBUG` | `false` | Flask debug mode. Never true in production. |
| `MAX_CONTENT_LENGTH` | `8388608` | Largest accepted request body, in bytes. |
| `DATA_DIR` | `(empty)` | Where uploaded and generated files live. |
| `INSTANCE_DIR` | `(empty)` | Where the SQLite file and instance state live. |
| `LOG_DIR` | `(empty)` | Where rotated log files are written, if file logging is on. |
| `LOG_LEVEL` | `INFO` | DEBUG \| INFO \| WARNING \| ERROR. |
| `LOG_JSON` | `true` | true emits one JSON object per line; false is human-readable. |
| `REQUEST_ID_HEADER` | `X-Request-ID` | Header echoed on every response and stamped on every log line. |

## Measured, not estimated

Produced on this checkout by `pytest --cov` and by booting `wsgi.py` and issuing one real GET per documented path. The commands are recorded in [`docs/EVIDENCE.md`](docs/EVIDENCE.md).

| Signal | Value |
| --- | --- |
| Tests | **23 / 23 passed** (2.3 s, exit 0) |
| Line coverage | **68.1%** — 448 of 628 statements |
| Source | 16 files / 1,431 lines |
| Test code | 4 files / 227 lines |
| Documented paths | 5 in the spec, 4 GET |
| Live probe | 13 GET requests to the booted app, **12 answered 200** |
| Median latency | **24.9 ms** (single uncached request, dev server) |
| Slowest / fastest | 10056.5 ms `/api/logs/stream` / 3.6 ms `/healthz` |
| Bytes served | 10.8 KB across 13 responses |
| Screenshots | 7 captured |

## How a request flows

```text
client
  │  HTTP
  ▼
wsgi.py ──▶ rlpa_server/app.py:get_app()
                │  reads config once (rlpa_server/config.py)
                │  registers the `proxy` blueprint
                ▼
           route handler
             ├──▶ rlpa_server/models.py        tables, via Flask-SQLAlchemy
             ├──▶ rlpa_server/errors.py        raises typed errors → one JSON envelope
             └──▶ rlpa_server/observability.py JSON log line + X-Request-ID
```

Every response carries `X-Request-ID`, and the matching log line is written once at the end of the request with the status and duration, so a report of "it failed" is one `grep` away from the traceback.

## Architecture

```
backlane/
├── src/rlpa_server/
│   ├── http.py                         379  HTTP plumbing for rlpa_server: correlation ids, acce
│   ├── proxy/api.py                    172  
│   ├── observability.py                169  Structured logging and request correlation for rlpa_
│   ├── config.py                       168  Environment-driven configuration for rlpa_server
│   ├── _app.py                         126  
│   ├── app.py                          119  Application factory for rlpa_server
│   ├── errors.py                       108  Typed application errors and their HTTP mapping for 
│   ├── paths.py                         52  Filesystem layout for rlpa_server
│   ├── models.py                        40  
│   ├── cli.py                           35  
│   ├── proxy/router.py                  24  
│   ├── proxy/ratelimit.py               19  
├── openapi/backlane.yaml                  the contract of record
├── schema/backlane.sql                    the DDL
├── tests/                       the suite that has to stay green
├── docs/EVIDENCE.md             the recorded live route walk
├── Dockerfile                   multi-stage build
└── wsgi.py                      entry point
```

The package keeps one shape across the service: `config.py` reads the environment once, `observability.py` emits structured JSON logs carrying a request id, `errors.py` turns exceptions into a single JSON envelope, `models.py` holds the tables, and the `proxy/` package holds the routes.

## Quality gates

| Gate | Command | Threshold |
| --- | --- | --- |
| Suite | `pytest -q` | all green |
| Coverage | `pytest --cov` | floor in `pyproject.toml`, set below the measured value |
| Lint | `ruff check src tests` | zero findings |
| Format | `ruff format --check src tests` | zero reformats |
| Types | `mypy src` | zero errors |
| Security | `bandit -c pyproject.toml -r src` | reviewed skip list, no unreviewed finding |
| Live routes | boot `wsgi.py`, one GET per documented path | no 5xx, no undocumented guard |

CI runs the first six on Python 3.11, 3.12 and 3.13 on every push to `main`, plus a container build — [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Development

```sh
pip install -e ".[dev]"
python -m pytest -q                      # the suite
python -m pytest --cov                   # with the coverage floor
python -m ruff check src tests           # lint
python -m ruff format --check src tests  # formatting
python -m mypy src                       # types
python -m bandit -c pyproject.toml -r src  # security
pre-commit install                       # the same checks on commit
```

Dependabot opens grouped PRs for the dev tooling weekly and for actions and the base image monthly.

## Deploy

```sh
docker build -t backlane .
docker run --rm -p 8000:8000 --env-file .env.example backlane
```

A `docker-compose.yml` is included for a local run with a volume for the SQLite file. The image runs as a non-root user and serves through gunicorn.

## Limits, stated rather than hidden

- HTTP/1.1 forwarding only; WebSocket upgrade is not proxied in this release.
- The proxy is a single process — horizontal scaling needs a shared database and sticky routing.

## License

MIT — see [LICENSE](LICENSE).
