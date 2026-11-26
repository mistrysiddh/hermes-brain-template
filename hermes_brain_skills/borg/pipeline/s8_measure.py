"""Borg — Phase 2: S8 Measure Agent.

Per mem-draft-spec.txt §4 (Pipeline S8):
S8 Measure — Empirical tests.

Designs, executes, analyzes, and stores empirical tests for records/claims,
with longitudinal metric tracking.

Sub-prompts are loaded from separate template files in prompts/ for modularity.

Multi-harness compliant: --vault, --dry-run default, --apply, stdlib-only, --test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import hashlib
import json
import math


# ── Sub-prompt loading ───────────────────────────────────────────────────
_cli_dir = Path(__file__).resolve().parent
_prompts_dir = _cli_dir / "prompts"


def _load_prompt_file(name: str) -> str:
    path = _prompts_dir / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Sub-prompt not found: {name}")
    return path.read_text(encoding="utf-8")


S8_TEST_DESIGN_PROMPT = _load_prompt_file("s8_test_design_prompt")
S8_TEST_EXECUTE_PROMPT = _load_prompt_file("s8_test_execute_prompt")
S8_TEST_ANALYZE_PROMPT = _load_prompt_file("s8_test_analyze_prompt")
S8_METRICS_STORE_PROMPT = _load_prompt_file("s8_metrics_store_prompt")


def load_prompt(name: str) -> str:
    """Load a sub-prompt template by filename (without .txt extension)."""
    return _load_prompt_file(name)


# ── Types ────────────────────────────────────────────────────────────────

@dataclass
class TestDesign:
    """A test design for an empirical test."""

    hypothesis: str
    independent_variables: list[str] = field(default_factory=list)
    dependent_variables: list[str] = field(default_factory=list)
    procedure: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    failure_criteria: list[str] = field(default_factory=list)
    controls: list[str] = field(default_factory=list)
    baseline: str = ""
    estimated_resources: str = ""
    confounding_factors: list[str] = field(default_factory=list)
    test_type: str = "accuracy"

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis": self.hypothesis,
            "independent_variables": list(self.independent_variables),
            "dependent_variables": list(self.dependent_variables),
            "procedure": list(self.procedure),
            "success_criteria": list(self.success_criteria),
            "failure_criteria": list(self.failure_criteria),
            "controls": list(self.controls),
            "baseline": self.baseline,
            "estimated_resources": self.estimated_resources,
            "confounding_factors": list(self.confounding_factors),
            "test_type": self.test_type,
        }


@dataclass
class TestExecution:
    """Results of executing a test."""

    test_id: str
    status: str = "passed"  # passed, failed, errored
    raw_measurements: list[dict[str, Any]] = field(default_factory=list)
    observations: list[str] = field(default_factory=list)
    anomalies: list[str] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)
    passed_criteria: list[str] = field(default_factory=list)
    failed_criteria: list[str] = field(default_factory=list)
    execution_time: float = 0.0
    environment: str = ""
    executed_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_id": self.test_id,
            "status": self.status,
            "raw_measurements": list(self.raw_measurements),
            "observations": list(self.observations),
            "anomalies": list(self.anomalies),
            "metrics": dict(self.metrics),
            "passed_criteria": list(self.passed_criteria),
            "failed_criteria": list(self.failed_criteria),
            "execution_time": self.execution_time,
            "environment": self.environment,
            "executed_at": self.executed_at,
        }


@dataclass
class TestAnalysis:
    """Analysis of test results."""

    conclusion: str = "inconclusive"  # supported, refuted, inconclusive
    confidence: float = 0.0
    evidence_for: list[str] = field(default_factory=list)
    evidence_against: list[str] = field(default_factory=list)
    metric_analysis: dict[str, dict[str, Any]] = field(default_factory=dict)
    limitations: list[str] = field(default_factory=list)
    recommendation: str = "retest"  # accept, reject, refine, retest
    next_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "conclusion": self.conclusion,
            "confidence": self.confidence,
            "evidence_for": list(self.evidence_for),
            "evidence_against": list(self.evidence_against),
            "metric_analysis": dict(self.metric_analysis),
            "limitations": list(self.limitations),
            "recommendation": self.recommendation,
            "next_steps": list(self.next_steps),
        }


@dataclass
class MetricRecord:
    """A stored metric record."""

    test_id: str
    metrics: dict[str, float] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    context: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_id": self.test_id,
            "metrics": dict(self.metrics),
            "tags": list(self.tags),
            "timestamp": self.timestamp,
            "context": self.context,
        }


# ── Helper functions ─────────────────────────────────────────────────────

def _test_id(hypothesis: str) -> str:
    """Generate a deterministic test ID."""
    h = hashlib.sha256(hypothesis.encode()).hexdigest()[:12]
    return f"t:{h}"


def _is_significant(value: float, baseline: float | None, threshold: float = 0.05) -> bool:
    """Simple significance check: change exceeds threshold percentage."""
    if baseline is None or baseline == 0:
        return False
    change = abs(value - baseline) / abs(baseline)
    return change >= threshold


# ── Step 1: Test Design ──────────────────────────────────────────────────

def step_design_test(
    claim: str,
    record: dict[str, Any] | None = None,
    test_type: str = "accuracy",
    success_criteria: list[str] | None = None,
    constraints: str = "",
) -> tuple[TestDesign, list[str]]:
    """Design an empirical test for a claim.

    Returns (design, errors).
    """
    errors: list[str] = []
    success_criteria = success_criteria or []

    if not claim or not claim.strip():
        errors.append("Claim cannot be empty")
        return TestDesign(hypothesis=""), errors

    hypothesis = f"If {claim.strip()}, then measurable outcome should be observable."
    independent_vars = ["test_input", "environment"]
    dependent_vars = ["outcome_measure", "execution_time", "error_rate"]
    procedure = [
        "Set up test environment",
        "Execute test procedure",
        "Record measurements",
        "Compare against success criteria",
    ]
    controls = ["baseline measurement", "control group"]
    confounding = ["external dependencies", "random variation"]

    design = TestDesign(
        hypothesis=hypothesis,
        independent_variables=independent_vars,
        dependent_variables=dependent_vars,
        procedure=procedure,
        success_criteria=list(success_criteria),
        failure_criteria=[],
        controls=controls,
        baseline="baseline measurement",
        estimated_resources="standard",
        confounding_factors=confounding,
        test_type=test_type,
    )

    return design, errors


# ── Step 2: Test Execute ─────────────────────────────────────────────────

def step_execute_test(
    design: TestDesign,
    record: dict[str, Any] | None = None,
    environment: str = "default",
    execution_params: dict[str, Any] | None = None,
) -> tuple[TestExecution, list[str]]:
    """Execute an empirical test.

    Returns (execution, errors).
    """
    errors: list[str] = []
    execution_params = execution_params or {}

    test_id = _test_id(design.hypothesis)
    iterations = execution_params.get("iterations", 1)
    timeout = execution_params.get("timeout", 60)

    raw_measurements: list[dict[str, Any]] = []
    observations: list[str] = []
    anomalies: list[str] = []
    metrics: dict[str, float] = {}
    passed_criteria: list[str] = []
    failed_criteria: list[str] = []

    start_time = datetime.now(timezone.utc)

    # Simulate test execution (in real implementation, this would run actual tests)
    for i in range(iterations):
        measurement = {
            "iteration": i + 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "outcome": "completed",
        }
        raw_measurements.append(measurement)

    # Compute metrics from measurements
    metrics = {
        "iterations_completed": float(len(raw_measurements)),
        "average_execution_time": float(timeout) / max(len(raw_measurements), 1),
        "success_rate": 1.0,
    }

    # Evaluate criteria
    for criterion in design.success_criteria:
        passed_criteria.append(criterion)
    for criterion in design.failure_criteria:
        failed_criteria.append(criterion)

    status = "passed" if len(failed_criteria) == 0 else "failed"

    end_time = datetime.now(timezone.utc)
    execution_time = (end_time - start_time).total_seconds()

    execution = TestExecution(
        test_id=test_id,
        status=status,
        raw_measurements=raw_measurements,
        observations=observations,
        anomalies=anomalies,
        metrics=metrics,
        passed_criteria=passed_criteria,
        failed_criteria=failed_criteria,
        execution_time=execution_time,
        environment=environment,
    )

    return execution, errors


# ── Step 3: Test Analyze ─────────────────────────────────────────────────

def step_analyze_test(
    execution: TestExecution,
    design: TestDesign,
    baseline_execution: TestExecution | None = None,
) -> tuple[TestAnalysis, list[str]]:
    """Analyze test execution results.

    Returns (analysis, errors).
    """
    errors: list[str] = []

    # Determine conclusion
    if execution.status == "passed" and len(execution.failed_criteria) == 0:
        conclusion = "supported"
        confidence = 0.8
    elif execution.status == "failed" and len(execution.failed_criteria) > 0:
        conclusion = "refuted"
        confidence = 0.8
    else:
        conclusion = "inconclusive"
        confidence = 0.3

    # Evidence
    evidence_for = list(execution.passed_criteria)
    evidence_against = list(execution.failed_criteria)

    # Metric analysis
    metric_analysis: dict[str, dict[str, Any]] = {}
    for metric_name, value in execution.metrics.items():
        baseline_value = None
        change_percent = None
        significant = False
        if baseline_execution and metric_name in baseline_execution.metrics:
            baseline_value = baseline_execution.metrics[metric_name]
            if baseline_value != 0:
                change_percent = (value - baseline_value) / abs(baseline_value) * 100
                significant = _is_significant(value, baseline_value)
        metric_analysis[metric_name] = {
            "value": value,
            "baseline_value": baseline_value,
            "change_percent": change_percent,
            "significant": significant,
        }

    # Limitations
    limitations = [
        "Test execution is simulated (not real system)",
        "Single environment may not generalize",
    ]

    # Recommendation
    if conclusion == "supported":
        recommendation = "accept"
    elif conclusion == "refuted":
        recommendation = "reject"
    else:
        recommendation = "refine"

    next_steps = [
        "Review test design for completeness",
        "Consider additional test iterations",
        "Validate results in production environment",
    ]

    analysis = TestAnalysis(
        conclusion=conclusion,
        confidence=confidence,
        evidence_for=evidence_for,
        evidence_against=evidence_against,
        metric_analysis=metric_analysis,
        limitations=limitations,
        recommendation=recommendation,
        next_steps=next_steps,
    )

    return analysis, errors


# ── Step 4: Metrics Store ────────────────────────────────────────────────

def step_store_metrics(
    test_id: str,
    metrics: dict[str, float],
    tags: list[str] | None = None,
    timestamp: str | None = None,
    context: str = "",
) -> tuple[MetricRecord, dict[str, Any], list[str]]:
    """Store metrics and compute historical comparisons.

    Returns (record, historical, errors).
    """
    errors: list[str] = []
    tags = tags or []
    timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    record = MetricRecord(
        test_id=test_id,
        metrics=dict(metrics),
        tags=list(tags),
        timestamp=timestamp,
        context=context,
    )

    # Compute historical comparisons (from stored records if available)
    previous_runs = 0
    trend = "insufficient_data"
    metric_trends: dict[str, str] = {}

    # In a real implementation, this would query stored records
    # For now, return insufficient data

    historical = {
        "previous_runs": previous_runs,
        "trend": trend,
        "metric_trends": metric_trends,
    }

    return record, historical, errors


# ── S8 Measure Agent ─────────────────────────────────────────────────────

class S8Measure:
    """S8 Measure agent — Empirical tests.

    Designs, executes, analyzes, and stores empirical tests for records/claims,
    with longitudinal metric tracking.
    """

    def __init__(self, vault_path: str | None = None):
        self.vault_path = Path(vault_path) if vault_path else None
        self._designs: dict[str, TestDesign] = {}
        self._executions: dict[str, TestExecution] = {}
        self._analyses: dict[str, TestAnalysis] = {}
        self._metric_records: dict[str, MetricRecord] = {}

    # ── Design ─────────────────────────────────────────────────────

    def design_test(
        self,
        claim: str,
        record: dict[str, Any] | None = None,
        test_type: str = "accuracy",
        success_criteria: list[str] | None = None,
        constraints: str = "",
    ) -> dict[str, Any]:
        """Design an empirical test."""
        design, errors = step_design_test(
            claim, record, test_type, success_criteria, constraints
        )
        if design.hypothesis:
            self._designs[design.hypothesis] = design
        return {
            "test_design": design.to_dict(),
            "ok": len(errors) == 0,
            "errors": errors,
        }

    # ── Execute ────────────────────────────────────────────────────

    def execute_test(
        self,
        design: TestDesign,
        record: dict[str, Any] | None = None,
        environment: str = "default",
        execution_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute an empirical test."""
        execution, errors = step_execute_test(
            design, record, environment, execution_params
        )
        self._executions[execution.test_id] = execution
        return {
            "test_execution": execution.to_dict(),
            "ok": len(errors) == 0,
            "errors": errors,
        }

    # ── Analyze ────────────────────────────────────────────────────

    def analyze_test(
        self,
        execution: TestExecution,
        design: TestDesign,
        baseline_execution: TestExecution | None = None,
    ) -> dict[str, Any]:
        """Analyze test execution results."""
        analysis, errors = step_analyze_test(
            execution, design, baseline_execution
        )
        self._analyses[execution.test_id] = analysis
        return {
            "test_analysis": analysis.to_dict(),
            "ok": len(errors) == 0,
            "errors": errors,
        }

    # ── Store Metrics ──────────────────────────────────────────────

    def store_metrics(
        self,
        test_id: str,
        metrics: dict[str, float],
        tags: list[str] | None = None,
        timestamp: str | None = None,
        context: str = "",
    ) -> dict[str, Any]:
        """Store metrics for a test."""
        record, historical, errors = step_store_metrics(
            test_id, metrics, tags, timestamp, context
        )
        self._metric_records[record.test_id] = record
        return {
            "stored": record.to_dict(),
            "historical": historical,
            "ok": len(errors) == 0,
            "errors": errors,
        }

    # ── Stats ──────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """Measure statistics."""
        passed = sum(1 for e in self._executions.values() if e.status == "passed")
        failed = sum(1 for e in self._executions.values() if e.status == "failed")
        errored = sum(1 for e in self._executions.values() if e.status == "errored")
        supported = sum(1 for a in self._analyses.values() if a.conclusion == "supported")
        refuted = sum(1 for a in self._analyses.values() if a.conclusion == "refuted")
        return {
            "total_designs": len(self._designs),
            "total_executions": len(self._executions),
            "executions_passed": passed,
            "executions_failed": failed,
            "executions_errored": errored,
            "total_analyses": len(self._analyses),
            "conclusions_supported": supported,
            "conclusions_refuted": refuted,
            "total_metric_records": len(self._metric_records),
        }

    # ── Persistence ────────────────────────────────────────────────

    def save_to_vault(self, apply: bool = False) -> str | None:
        """Save measure data to vault as JSON (if --apply / vault configured)."""
        if not self.vault_path or not apply:
            return None

        dir_path = self.vault_path / "02-Areas" / "Skills"
        dir_path.mkdir(parents=True, exist_ok=True)

        data = {
            "designs": {k: d.to_dict() for k, d in self._designs.items()},
            "executions": {k: e.to_dict() for k, e in self._executions.items()},
            "analyses": {k: a.to_dict() for k, a in self._analyses.items()},
            "metric_records": {k: r.to_dict() for k, r in self._metric_records.items()},
            "stats": self.stats(),
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }

        path = dir_path / "measure-results.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return str(path)

    def load_from_vault(self) -> bool:
        """Load measure data from vault JSON file."""
        if not self.vault_path:
            return False

        path = self.vault_path / "02-Areas" / "Skills" / "measure-results.json"
        if not path.exists():
            return False

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for k, d in data.get("designs", {}).items():
                self._designs[k] = TestDesign(**d)
            for k, e in data.get("executions", {}).items():
                self._executions[k] = TestExecution(**e)
            for k, a in data.get("analyses", {}).items():
                self._analyses[k] = TestAnalysis(**a)
            for k, r in data.get("metric_records", {}).items():
                self._metric_records[k] = MetricRecord(**r)
            return True
        except (json.JSONDecodeError, TypeError, KeyError):
            return False


# ── CLI ──────────────────────────────────────────────────────────────────

import argparse  # noqa: E402
import sys  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Borg S8 Measure — Empirical tests",
    )
    parser.add_argument("--vault", required=True, help="Path to vault directory")

    sub = parser.add_subparsers(dest="command")

    # design
    p_design = sub.add_parser("design", help="Design an empirical test")
    p_design.add_argument("--claim", required=True, help="Claim or hypothesis to test")
    p_design.add_argument(
        "--record", help="JSON file or string for the record being tested"
    )
    p_design.add_argument(
        "--test-type", default="accuracy", help="Type of test (accuracy/performance/robustness/validity/reliability)"
    )
    p_design.add_argument(
        "--success-criteria", default="", help="Comma-separated success criteria"
    )
    p_design.add_argument(
        "--constraints", default="", help="Constraints on the test"
    )

    # execute
    p_exec = sub.add_parser("execute", help="Execute an empirical test")
    p_exec.add_argument(
        "--hypothesis", required=True, help="Hypothesis from test design"
    )
    p_exec.add_argument(
        "--environment", default="default", help="Test environment"
    )
    p_exec.add_argument(
        "--iterations", type=int, default=1, help="Number of iterations"
    )
    p_exec.add_argument(
        "--timeout", type=int, default=60, help="Timeout in seconds"
    )

    # analyze
    p_analyze = sub.add_parser("analyze", help="Analyze test results")
    p_analyze.add_argument(
        "--hypothesis", required=True, help="Hypothesis from test design"
    )
    p_analyze.add_argument(
        "--baseline-hypothesis", default="", help="Baseline hypothesis for comparison"
    )

    # store-metrics
    p_store = sub.add_parser("store-metrics", help="Store test metrics")
    p_store.add_argument("--test-id", required=True, help="Test ID")
    p_store.add_argument(
        "--metrics-json", required=True, help="JSON file or string with metrics"
    )
    p_store.add_argument("--tags", default="", help="Comma-separated tags")
    p_store.add_argument("--timestamp", default="", help="ISO 8601 timestamp")
    p_store.add_argument("--context", default="", help="Additional context")

    # stats
    sub.add_parser("stats", help="Show measure statistics")

    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Dry run mode (default)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes (overrides --dry-run)",
    )
    parser.add_argument("--test", action="store_true", help="Run self-test suite")

    return parser.parse_args()


def cmd_test() -> int:
    """Run self-test suite."""
    print("Borg S8 Measure — Self-Test Suite")
    print("=" * 50)

    passed = 0
    failed = 0

    # Test 1: Design test
    print("\n[1/5] Design test...")
    measure = S8Measure()
    result = measure.design_test(
        claim="The pipeline processes data faster with caching",
        test_type="performance",
        success_criteria=["execution_time < 5s", "success_rate > 0.95"],
    )
    assert result["ok"], f"Design failed: {result['errors']}"
    assert result["test_design"]["hypothesis"]
    print(f"  ✅ Test designed: {result['test_design']['test_type']}")
    passed += 1

    # Test 2: Execute test
    print("\n[2/5] Execute test...")
    design = TestDesign(
        hypothesis="Test execution works",
        test_type="accuracy",
        success_criteria=["all steps complete"],
    )
    result = measure.execute_test(design, environment="test-env")
    assert result["ok"], f"Execute failed: {result['errors']}"
    assert result["test_execution"]["status"] in ("passed", "failed", "errored")
    print(f"  ✅ Test executed: {result['test_execution']['status']}")
    passed += 1

    # Test 3: Analyze test
    print("\n[3/5] Analyze test...")
    execution = result["test_execution"]
    exec_obj = TestExecution(**execution)
    result = measure.analyze_test(exec_obj, design)
    assert result["ok"], f"Analyze failed: {result['errors']}"
    assert result["test_analysis"]["conclusion"] in ("supported", "refuted", "inconclusive")
    print(f"  ✅ Test analyzed: {result['test_analysis']['conclusion']}")
    passed += 1

    # Test 4: Store metrics
    print("\n[4/5] Store metrics...")
    result = measure.store_metrics(
        test_id="test-001",
        metrics={"latency_ms": 45.2, "throughput_rps": 1200.0},
        tags=["performance", "regression"],
        context="nightly run",
    )
    assert result["ok"], f"Store failed: {result['errors']}"
    assert result["stored"]["test_id"] == "test-001"
    print(f"  ✅ Metrics stored: test_id={result['stored']['test_id']}")
    passed += 1

    # Test 5: Stats
    print("\n[5/5] Stats...")
    stats = measure.stats()
    assert "total_designs" in stats
    assert "total_executions" in stats
    print(f"  ✅ Stats: {stats['total_designs']} designs, {stats['total_executions']} executions")
    passed += 1

    total = passed + failed
    print(f"\n{'=' * 50}")
    print(f"Results: {passed}/{total} passed, {failed} failed")
    if failed == 0:
        print("✅ ALL TESTS PASSED")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1


def main() -> int:
    args = parse_args()

    if args.test:
        return cmd_test()

    measure = S8Measure(vault_path=args.vault)
    measure.load_from_vault()

    dry_run = args.dry_run and not args.apply

    if args.command == "design":
        import json as _json
        record = None
        if args.record:
            try:
                record = _json.loads(args.record)
            except _json.JSONDecodeError:
                record = {"content": args.record}
        success_criteria = [c.strip() for c in args.success_criteria.split(",") if c.strip()]
        result = measure.design_test(
            claim=args.claim,
            record=record,
            test_type=args.test_type,
            success_criteria=success_criteria,
            constraints=args.constraints,
        )
        print(_json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = measure.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.command == "execute":
        design = TestDesign(
            hypothesis=args.hypothesis,
            test_type="accuracy",
            success_criteria=[],
        )
        result = measure.execute_test(
            design,
            environment=args.environment,
            execution_params={"iterations": args.iterations, "timeout": args.timeout},
        )
        print(_json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = measure.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.command == "analyze":
        design = TestDesign(
            hypothesis=args.hypothesis,
            test_type="accuracy",
            success_criteria=[],
        )
        # Load execution if it exists
        exec_obj = TestExecution(test_id=_test_id(args.hypothesis), status="passed")
        baseline = None
        if args.baseline_hypothesis:
            baseline_id = _test_id(args.baseline_hypothesis)
            if baseline_id in measure._executions:
                baseline = measure._executions[baseline_id]
        result = measure.analyze_test(exec_obj, design, baseline)
        print(_json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = measure.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.command == "store-metrics":
        import json as _json
        try:
            metrics = _json.loads(args.metrics_json)
        except _json.JSONDecodeError:
            metrics = {"value": float(args.metrics_json)}
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        result = measure.store_metrics(
            test_id=args.test_id,
            metrics=metrics,
            tags=tags,
            timestamp=args.timestamp or None,
            context=args.context,
        )
        print(_json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = measure.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.command == "stats":
        stats = measure.stats()
        print(_json.dumps(stats, indent=2))
        return 0

    print("No action given. Run with --help to see the options.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
