from flask import Flask, jsonify, redirect, render_template, request, url_for

from . import paths
from .models import db
from .proxy.api import bp

# Templates ship at the project root (templates/), one level above this module,
# and the sqlite file is written under instance/.  Flask defaults both to the
# package folder, which is why an app built without these kwargs raises
# TemplateNotFound for every page.
paths.ensure_runtime_dirs()


def build_app():
    """Build the application: configuration, database, then routes."""
    app = Flask(
        __name__, template_folder=str(paths.TEMPLATES_DIR), instance_path=str(paths.INSTANCE_DIR)
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(paths.INSTANCE_DIR / "rlpa.db")
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.register_blueprint(bp)

    def _page_context():
        """Counts and url_for-resolved nav links, shared by every page.

        links holds real route URLs so the templates never need href="#"
        placeholders; the current page is styled active instead.
        """
        from .models import AccessLog, Route

        return {
            "app_name": "rlpa-server",
            "links": {
                "index": url_for("index"),
                "logs": url_for("logs_page"),
                "health": url_for("health"),
            },
            "counts": {
                "routes": Route.query.count(),
                "logs": AccessLog.query.count(),
                "stream": url_for("proxy.log_stream"),
                "export": url_for("proxy.export"),
            },
        }

    @app.get("/")
    def index():
        """Route table rendered from the real Route / AccessLog tables."""
        from .models import AccessLog, Route

        routes = Route.query.order_by(Route.id).all()
        last_log = {}
        for row in AccessLog.query.order_by(AccessLog.id.desc()).limit(200).all():
            last_log.setdefault(row.route_id, row)
        ctx = _page_context()
        ctx.update({"routes": routes, "last_log": last_log, "log_count": ctx["counts"]["logs"]})
        return render_template("index.html", **ctx)

    @app.get("/logs")
    def logs_page():
        """Access-log viewer; the q= filter goes straight into the query."""
        from .models import AccessLog

        q = (request.args.get("q") or "").strip()
        query = AccessLog.query
        if q:
            query = query.filter(AccessLog.path.contains(q))
        rows = query.order_by(AccessLog.id.desc()).limit(200).all()
        ctx = _page_context()
        ctx.update({"rows": rows, "q": q})
        return render_template("logs.html", **ctx)

    @app.get("/health")
    def health():
        """Liveness probe used by the footer of the base template."""
        from .models import AccessLog, Route

        return jsonify(
            {"status": "ok", "routes": Route.query.count(), "logs": AccessLog.query.count()}
        )

    @app.post("/route/add")
    def route_add_form():
        """HTML twin of POST /api/routes, for the form on the index page."""
        from .models import Route

        form = request.form
        host = (form.get("host") or "").strip()
        upstream = (form.get("upstream") or "").strip()
        if host and upstream:
            try:
                rate = int(form.get("rate") or 100)
            except ValueError:
                rate = 100
            db.session.add(
                Route(
                    host=host,
                    path=(form.get("path") or "/").strip() or "/",
                    upstream=upstream,
                    auth=form.get("auth") or "none",
                    rate_limit=rate,
                )
            )
            db.session.commit()
        return redirect(url_for("index"))

    @app.post("/route/<int:rid>/delete")
    def route_delete_form(rid):
        """HTML twin of DELETE /api/routes/<rid>, for the row delete button."""
        from .models import Route

        obj = db.session.get(Route, rid)
        if obj is not None:
            db.session.delete(obj)
            db.session.commit()
        return redirect(url_for("index"))

    return app


app = build_app()
