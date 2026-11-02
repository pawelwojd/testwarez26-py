# testwarez26-py
testwarez workshop

## SWAPI starship tests

Tests for the [Star Wars API](https://swapi.dev) `/starships` endpoint. They use only the Python standard library (`unittest` + `urllib`), so you don't need to install anything. Requires Python 3.10+ and network access.

```
swapi_tests/
  client.py                       # small SWAPI client (caching, retries, number parsing)
  tests/
    test_starships_endpoint.py    # list/pagination/schema/404 contract
    test_starship_types.py        # data per ship type: starfighters, freighters,
                                  #   capital ships, battlestations
    test_starship_search.py       # ?search= behaviour
runner/                           # separate test-runner module + HTML report
```

### Run

```bash
python -m runner                  # run everything, write reports/report_<timestamp>.html
python -m runner --open           # ...and open the report in a browser
python -m runner -k death         # only tests whose name contains "death"
python -m runner --report out.html -q
SWAPI_BASE_URL=https://swapi.info/api python -m runner   # point at a mirror
```

The exit code is 0 when everything passes and 1 when anything fails or errors. The tests also run under plain `python -m unittest discover -s swapi_tests/tests -t .` or PyCharm's test runner.

The HTML report is one self-contained file. It shows stat tiles, an overall pass/fail bar, a breakdown by suite (ship type), the slowest tests, and a filterable results table with tracebacks. It follows your system's light or dark theme.
