"""Export current metrics to stdout."""
from __future__ import annotations

from pprint import pprint

from ..db import create_all, session_scope
from ..routers.tagging import compute_metrics


def main() -> None:
    create_all()
    with session_scope() as db:
        metrics = compute_metrics(db)
    pprint(metrics)


if __name__ == "__main__":
    main()
