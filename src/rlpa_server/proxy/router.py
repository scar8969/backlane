import httpx

def match(host, path):
    from .models import Route
    # exact host+path first
    r = Route.query.filter_by(host=host, path=path).first()
    if r:
        return r
    # wildcard /api/* routes
    for route in Route.query.filter_by(host=host).all():
        if route.path.endswith("/*") and path.startswith(route.path[:-1]):
            return route
    return None

def forward(route, method, path, headers, body):
    url = route.upstream.rstrip("/") + path
    hdrs = {k: v for k, v in headers.items() if not k.lower().startswith("x-internal")}
    hdrs["X-Forwarded-Host"] = route.host
    with httpx.Client(timeout=30) as c:
        return c.request(method, url, headers=hdrs, content=body)
