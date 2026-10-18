from flask import Blueprint, Response, jsonify, request

from ..models import AccessLog, Route, db
from .auth import require_auth
from .ratelimit import SlidingWindow
from .router import forward, match

bp = Blueprint("proxy", __name__)
_limiters = {}


@bp.post("/api/routes")
def add_route():
    d = request.get_json(force=True, silent=True) or {}
    r = Route(
        host=d.get("host", ""),
        path=d.get("path", "/"),
        upstream=d.get("upstream", ""),
        auth=d.get("auth", "none"),
        rate_limit=d.get("rate", 100),
    )
    db.session.add(r)
    db.session.commit()
    return jsonify({"id": r.id})


@bp.get("/api/routes")
def list_routes():
    return jsonify(
        {
            "routes": [
                {
                    "id": r.id,
                    "host": r.host,
                    "path": r.path,
                    "upstream": r.upstream,
                    "auth": r.auth,
                    "rate": r.rate_limit,
                }
                for r in Route.query.all()
            ]
        }
    )


@bp.delete("/api/routes/<int:rid>")
def delete_route(rid):
    r = Route.query.get_or_404(rid)
    db.session.delete(r)
    db.session.commit()
    return jsonify({"status": "deleted"})


@bp.get("/api/logs")
def logs():
    q = request.args.get("q", "")
    query = AccessLog.query
    if q:
        query = query.filter(AccessLog.path.contains(q) | AccessLog.user.contains(q))
    rows = [
        {
            "id": l.id,
            "method": l.method,
            "path": l.path,
            "user": l.user,
            "status": l.status,
            "ms": l.ms,
            "at": l.at.isoformat() if l.at else "",
        }
        for l in query.order_by(AccessLog.id.desc()).limit(100).all()
    ]
    return jsonify({"logs": rows})


@bp.get("/api/logs/stream")
def log_stream():
    # A streaming response is consumed by the WSGI server after the view
    # returns, so the request context is already gone by the time the
    # generator body runs.  Resolve the real app object here (inside the
    # request) and push an application context from inside the generator,
    # otherwise every query raises "Working outside of application context".
    from flask import current_app

    _app = current_app._get_current_object()

    def gen():
        with _app.app_context():
            last = 0
            ticks = 0
            # A streaming response is read to completion by any plain WSGI
            # client (and by a probe), so the window is short and FINITE: ten
            # one-second ticks.  EventSource reconnects by itself, which is how
            # a browser keeps a live tail open past the window.
            while ticks < 10:
                rows = (
                    AccessLog.query.filter(AccessLog.id > last)
                    .order_by(AccessLog.id)
                    .limit(20)
                    .all()
                )
                for r in rows:
                    last = r.id
                    yield f"data: {r.method} {r.path} {r.user} {r.status} {r.ms}ms\n\n"
                ticks += 1
                # A comment line is ignored by EventSource, but it gives an
                # idle log table a byte per tick so the stream is provably
                # alive instead of silent for the whole window.
                yield f": keepalive {ticks}\n\n"
                import time

                time.sleep(1)
            yield "event: close\ndata: stream window ended\n\n"

    return Response(
        gen(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@bp.get("/api/logs/export")
def export():
    import csv
    import io

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["time", "method", "path", "user", "status", "ms"])
    for l in AccessLog.query.limit(1000).all():
        w.writerow([l.at.isoformat() if l.at else "", l.method, l.path, l.user, l.status, l.ms])
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=logs.csv"},
    )


@bp.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy(path):
    route = match(request.host, "/" + path)
    if not route:
        return jsonify({"error": "not_found"}), 404
    user = require_auth(route, request)
    if route.auth != "none" and not user:
        return jsonify({"error": "unauthorized"}), 401
    limiter = _limiters.setdefault(route.id, SlidingWindow(route.rate_limit, route.rate_window))
    if limiter.hit(user.username if user else request.remote_addr):
        return jsonify({"error": "rate limited"}), 429
    import time

    t0 = time.perf_counter()
    try:
        resp = forward(route, request.method, "/" + path, dict(request.headers), request.get_data())
        status = resp.status_code
    except Exception:
        status = 502
    db.session.add(
        AccessLog(
            route_id=route.id,
            user=user.username if user else "",
            method=request.method,
            path="/" + path,
            status=status,
            ms=int((time.perf_counter() - t0) * 1000),
            ip=request.remote_addr or "",
        )
    )
    db.session.commit()
    return jsonify({"status": status})
