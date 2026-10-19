import argparse


def cmd_route_add(args):
    # Imported inside the command, not at module scope: only the web layer
    # needs the ORM, and the lazy import keeps `python cli.py --help` working
    # on an interpreter where flask_sqlalchemy is not installed.
    from .models import Route, db

    r = Route(host=args.host, upstream=args.upstream, auth=args.auth, rate_limit=args.rate)
    db.session.add(r)
    db.session.commit()
    print(f"route added: {args.host} → {args.upstream} (auth {args.auth}, rate {args.rate})")


def main():
    p = argparse.ArgumentParser(prog="rlpa")
    sub = p.add_subparsers(dest="cmd")
    r = sub.add_parser("route")
    rs = r.add_subparsers(dest="sub")
    a = rs.add_parser("add")
    a.add_argument("host")
    a.add_argument("upstream")
    a.add_argument("--auth", default="none")
    a.add_argument("--rate", type=int, default=100)
    args = p.parse_args()
    if args.cmd == "route" and args.sub == "add":
        return cmd_route_add(args)
    p.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover - manual entry point
    raise SystemExit(main())
