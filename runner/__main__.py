"""CLI entry point:  python -m runner [options]"""

from __future__ import annotations

import argparse
import sys
import webbrowser

from runner.report import write_report
from runner.runner import run_tests


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m runner", description="Run SWAPI tests and build an HTML report.")
    parser.add_argument("--start-dir", default="swapi_tests/tests", help="directory to discover tests in")
    parser.add_argument("--pattern", default="test_*.py", help="test file glob (default: test_*.py)")
    parser.add_argument("-k", dest="name_filter", action="append",
                        help="only run tests whose name contains this substring (repeatable)")
    parser.add_argument("--report", default=None,
                        help="report path (default: reports/report_<timestamp>.html)")
    parser.add_argument("--open", action="store_true", help="open the report in a browser when done")
    parser.add_argument("-q", "--quiet", action="store_true", help="less console output")
    args = parser.parse_args(argv)

    summary = run_tests(start_dir=args.start_dir, pattern=args.pattern,
                        verbosity=1 if args.quiet else 2, name_filter=args.name_filter)

    from swapi_tests.client import client  # imported after discovery so SWAPI_BASE_URL is honoured
    report_path = args.report or f"reports/report_{summary.started_at:%Y%m%d_%H%M%S}.html"
    path = write_report(summary, report_path, base_url=client.base_url)

    print(f"\n{summary.count('passed')} passed, {summary.count('failed')} failed, "
          f"{summary.count('error')} errors, {summary.count('skipped')} skipped "
          f"in {summary.duration:.2f}s")
    print(f"HTML report: {path.resolve()}")
    if args.open:
        webbrowser.open(path.resolve().as_uri())
    return 0 if summary.successful else 1


if __name__ == "__main__":
    sys.exit(main())
