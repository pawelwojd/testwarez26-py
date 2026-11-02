"""Discover and run unittest tests, recording per-test outcome and timing."""

from __future__ import annotations

import sys
import time
import traceback
import unittest
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TestRecord:
    test_id: str
    suite: str          # TestCase class name, e.g. "TestStarfighters"
    module: str         # module name, e.g. "test_starship_types"
    name: str           # method name
    description: str
    outcome: str = "passed"   # passed | failed | error | skipped
    duration: float = 0.0
    details: str = ""


@dataclass
class RunSummary:
    started_at: datetime
    duration: float = 0.0
    records: list[TestRecord] = field(default_factory=list)

    def count(self, outcome: str) -> int:
        return sum(1 for r in self.records if r.outcome == outcome)

    @property
    def total(self) -> int:
        return len(self.records)

    @property
    def successful(self) -> bool:
        return self.count("failed") == 0 and self.count("error") == 0


class RecordingResult(unittest.TextTestResult):
    """TextTestResult that also keeps a structured record of every test."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records: list[TestRecord] = []
        self._current: TestRecord | None = None
        self._t0 = 0.0

    def _fmt(self, err) -> str:
        return "".join(traceback.format_exception(*err))

    def startTest(self, test):
        super().startTest(test)
        cls = type(test)
        self._current = TestRecord(
            test_id=test.id(),
            suite=cls.__name__,
            module=cls.__module__.rsplit(".", 1)[-1],
            name=getattr(test, "_testMethodName", str(test)),
            description=(test.shortDescription() or ""),
        )
        self._t0 = time.perf_counter()

    def stopTest(self, test):
        if self._current is not None:
            self._current.duration = time.perf_counter() - self._t0
            self.records.append(self._current)
            self._current = None
        super().stopTest(test)

    def _mark(self, outcome: str, details: str):
        if self._current is None:  # e.g. setUpClass failure, reported against a placeholder
            return
        # Keep the worst outcome if a test reports several (e.g. multiple failing subTests).
        rank = {"passed": 0, "skipped": 1, "failed": 2, "error": 3}
        if rank[outcome] >= rank[self._current.outcome]:
            self._current.outcome = outcome
        if details:
            self._current.details += (("\n" + "-" * 60 + "\n") if self._current.details else "") + details

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._mark("failed", self._fmt(err))

    def addError(self, test, err):
        super().addError(test, err)
        if self._current is None:
            # Class/module-level fixture error (setUpClass etc.): record it as its own entry.
            self.records.append(TestRecord(
                test_id=str(test), suite=str(test).split(" ")[-1].strip("()").rsplit(".", 1)[-1],
                module="", name=str(test).split(" ")[0], description="Fixture error",
                outcome="error", details=self._fmt(err),
            ))
            return
        self._mark("error", self._fmt(err))

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._mark("skipped", reason)

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            outcome = "failed" if issubclass(err[0], test.failureException) else "error"
            self._mark(outcome, f"{subtest._subDescription()}\n{self._fmt(err)}")

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self._mark("failed", "Unexpected success (test was marked expectedFailure)")


def run_tests(start_dir: str = "swapi_tests/tests", pattern: str = "test_*.py",
              top_level_dir: str | None = ".", verbosity: int = 2,
              name_filter: list[str] | None = None) -> RunSummary:
    loader = unittest.TestLoader()
    if name_filter:
        loader.testNamePatterns = [f"*{p}*" for p in name_filter]
    suite = loader.discover(start_dir=start_dir, pattern=pattern, top_level_dir=top_level_dir)

    summary = RunSummary(started_at=datetime.now())
    runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=verbosity, resultclass=RecordingResult)
    t0 = time.perf_counter()
    result: RecordingResult = runner.run(suite)  # type: ignore[assignment]
    summary.duration = time.perf_counter() - t0
    summary.records = result.records
    return summary
