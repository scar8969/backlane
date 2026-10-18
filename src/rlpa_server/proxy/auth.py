def require_auth(route, request):
    from flask import session

    from .models import User

    if route.auth == "api-key":
        key = request.headers.get("X-API-Key", "")
        return User.query.filter_by(api_key=key).first()
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None
