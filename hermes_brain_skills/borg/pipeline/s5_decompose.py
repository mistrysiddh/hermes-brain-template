"""Borg — Phase 2: S5 Decompose Agent.

Per mem-draft-spec.txt §4 (Pipeline S5):
S5 Decompose — Composites → DAGs.

Detects composite tasks, decomposes them into units, maps dependencies,
builds DAGs, and determines topological execution order.

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
import re


# ── Sub-prompt loading ───────────────────────────────────────────────────
_cli_dir = Path(__file__).resolve().parent
_prompts_dir = _cli_dir / "prompts"


def _load_prompt_file(name: str) -> str:
    path = _prompts_dir / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Sub-prompt not found: {name}")
    return path.read_text(encoding="utf-8")


S5_COMPOSITE_DETECT_PROMPT = _load_prompt_file("s5_composite_detect_prompt")
S5_DAG_BUILD_PROMPT = _load_prompt_file("s5_dag_build_prompt")
S5_DEPENDENCY_MAP_PROMPT = _load_prompt_file("s5_dependency_map_prompt")
S5_EXECUTION_ORDER_PROMPT = _load_prompt_file("s5_execution_order_prompt")


def load_prompt(name: str) -> str:
    """Load a sub-prompt template by filename (without .txt extension)."""
    return _load_prompt_file(name)


# ── Types ────────────────────────────────────────────────────────────────

UNIT_TYPES = {"action", "research", "analysis", "verification", "coordination"}

DEPENDENCY_TYPES = {"sequential", "data", "control", "resource"}

DEPENDENCY_STRENGTHS = {"weak", "medium", "strong"}


@dataclass
class Composite:
    """A composite task detected from raw content."""

    id: str
    text: str
    domain: str
    complexity: float
    step_estimate: int
    source_location: str
    size: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "domain": self.domain,
            "complexity": self.complexity,
            "step_estimate": self.step_estimate,
            "source_location": self.source_location,
            "size": self.size,
        }


@dataclass
class Unit:
    """A decomposed unit within a composite."""

    id: str
    text: str
    type: str
    estimated_duration: int
    dependencies: list[str] = field(default_factory=list)
    dependents: list[str] = field(default_factory=list)
    level: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "type": self.type,
            "estimated_duration": self.estimated_duration,
            "dependencies": list(self.dependencies),
            "dependents": list(self.dependents),
            "level": self.level,
        }


@dataclass
class Dependency:
    """A dependency between two units."""

    from_unit: str
    to_unit: str
    type: str
    strength: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "from": self.from_unit,
            "to": self.to_unit,
            "type": self.type,
            "strength": self.strength,
            "rationale": self.rationale,
        }


@dataclass
class DAG:
    """A directed acyclic graph of units."""

    composite_id: str
    nodes: dict[str, Unit] = field(default_factory=dict)
    edges: list[tuple[str, str]] = field(default_factory=list)
    is_acyclic: bool = True
    total_levels: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "composite_id": self.composite_id,
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "edges": [{"from": f, "to": t} for f, t in self.edges],
            "roots": sorted(self._roots()),
            "leaves": sorted(self._leaves()),
            "total_levels": self.total_levels,
            "is_acyclic": self.is_acyclic,
        }

    def _roots(self) -> list[str]:
        """Nodes with no dependencies."""
        return [nid for nid, n in self.nodes.items() if not n.dependencies]

    def _leaves(self) -> list[str]:
        """Nodes with no dependents."""
        return [nid for nid, n in self.nodes.items() if not n.dependents]


@dataclass
class ExecutionWave:
    """A wave of units executable in parallel."""

    wave: int
    units: list[str]
    estimated_wave_duration: int


@dataclass
class ExecutionPlan:
    """Execution plan derived from a DAG."""

    waves: list[ExecutionWave] = field(default_factory=list)
    critical_path: list[str] = field(default_factory=list)
    total_estimated_duration: int = 0
    total_waves: int = 0
    parallelizable_units: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_order": [
                {
                    "wave": w.wave,
                    "units": list(w.units),
                    "estimated_wave_duration": w.estimated_wave_duration,
                }
                for w in self.waves
            ],
            "critical_path": list(self.critical_path),
            "total_estimated_duration": self.total_estimated_duration,
            "total_waves": self.total_waves,
            "parallelizable_units": self.parallelizable_units,
        }


# ── Helper functions ─────────────────────────────────────────────────────

def _composite_id(text: str) -> str:
    """Generate a deterministic composite ID from text."""
    h = hashlib.sha256(text.encode()).hexdigest()[:12]
    return f"c:{h}"


def _unit_id(composite_id: str, index: int) -> str:
    """Generate a deterministic unit ID."""
    return f"u:{composite_id}:{index}"


def _split_into_units(text: str) -> list[str]:
    """Split composite text into decomposed units."""
    units: list[str] = []
    # Split by sentences and bullet points
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    for sent in sentences:
        sent = sent.strip()
        if sent:
            units.append(sent)
    # Also split by bullet markers
    for unit in list(units):
        bullets = re.split(r"\n[-*•]\s+", unit)
        if len(bullets) > 1:
            units.remove(unit)
            for b in bullets:
                b = b.strip()
                if b:
                    units.append(b)
    return units


def _classify_unit_type(text: str) -> str:
    """Classify a unit by type."""
    lower = text.lower()
    if any(kw in lower for kw in ["research", "investigate", "study", "explore"]):
        return "research"
    if any(kw in lower for kw in ["analyze", "review", "audit", "assess"]):
        return "analysis"
    if any(kw in lower for kw in ["verify", "test", "check", "validate", "confirm"]):
        return "verification"
    if any(kw in lower for kw in ["coordinate", "communicate", "notify", "report"]):
        return "coordination"
    return "action"


def _estimate_duration(text: str) -> int:
    """Estimate duration in minutes for a unit."""
    # Base: 15 minutes per unit, adjust by length and complexity keywords
    base = 15
    length_factor = min(len(text) / 100, 2.0)
    complexity_kw = ["complex", "difficult", "extensive", "thorough", "comprehensive"]
    kw_bonus = sum(5 for kw in complexity_kw if kw in text.lower())
    return int(base + length_factor * 10 + kw_bonus)


def _topological_sort(dag: DAG) -> list[str]:
    """Topological sort of DAG nodes using Kahn's algorithm."""
    in_degree: dict[str, int] = {nid: 0 for nid in dag.nodes}
    adj: dict[str, list[str]] = {nid: [] for nid in dag.nodes}

    for from_nid, to_nid in dag.edges:
        adj[from_nid].append(to_nid)
        in_degree[to_nid] = in_degree.get(to_nid, 0) + 1

    queue = [nid for nid, deg in in_degree.items() if deg == 0]
    result: list[str] = []

    while queue:
        queue.sort()  # deterministic order
        nid = queue.pop(0)
        result.append(nid)
        for neighbor in adj.get(nid, []):
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return result


def _detect_cycle(dag: DAG) -> bool:
    """Detect if the DAG has a cycle using DFS."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {nid: WHITE for nid in dag.nodes}
    adj: dict[str, list[str]] = {nid: [] for nid in dag.nodes}

    for from_nid, to_nid in dag.edges:
        adj[from_nid].append(to_nid)

    def dfs(nid: str) -> bool:
        color[nid] = GRAY
        for neighbor in adj.get(nid, []):
            if color[neighbor] == GRAY:
                return True  # cycle found
            if color[neighbor] == WHITE and dfs(neighbor):
                return True
        color[nid] = BLACK
        return False

    for nid in dag.nodes:
        if color[nid] == WHITE:
            if dfs(nid):
                return True
    return False


# ── Step 1: Composite Detect ─────────────────────────────────────────────

def step_detect_composites(
    content: str,
    min_size: int = 100,
) -> tuple[list[Composite], list[str]]:
    """Detect composite tasks from content.

    Returns (composites, errors).
    """
    errors: list[str] = []
    composites: list[Composite] = []

    if not content or not content.strip():
        return [], ["Content is empty"]

    # Split content into candidate composites (paragraphs)
    paragraphs = re.split(r"\n\s*\n", content.strip())
    composite_keywords = [
        "and then", "followed by", "after", "then", "next",
        "step", "first", "second", "finally", "pipeline",
        "workflow", "process", "procedure",
    ]

    for i, para in enumerate(paragraphs):
        para = para.strip()
        if not para:
            continue
        if len(para) < min_size:
            continue

        # Check if it looks like a composite (multi-step language)
        lower = para.lower()
        has_composite_signal = any(kw in lower for kw in composite_keywords)
        sentence_count = len(re.split(r"(?<=[.!?])\s+", para))

        if not has_composite_signal and sentence_count < 2:
            continue  # Not a composite, likely a single atomic action

        domain = _classify_domain(para)
        complexity = _compute_complexity(para, sentence_count)
        step_estimate = max(sentence_count, 2)

        composites.append(Composite(
            id="",  # assigned later
            text=para,
            domain=domain,
            complexity=complexity,
            step_estimate=step_estimate,
            source_location=f"paragraph-{i}",
            size=len(para),
        ))

    # Sort by complexity descending
    composites.sort(key=lambda c: c.complexity, reverse=True)

    # Assign IDs
    for i, c in enumerate(composites):
        c.id = _composite_id(c.text)

    return composites, errors


def _classify_domain(text: str) -> str:
    """Classify composite by domain."""
    lower = text.lower()
    if any(kw in lower for kw in ["code", "implement", "build", "develop", "program"]):
        return "implementation"
    if any(kw in lower for kw in ["research", "investigate", "study", "explore"]):
        return "research"
    if any(kw in lower for kw in ["analyze", "review", "audit", "assess"]):
        return "analysis"
    if any(kw in lower for kw in ["deploy", "operate", "maintain", "monitor"]):
        return "operations"
    return "general"


def _compute_complexity(text: str, sentence_count: int) -> float:
    """Compute complexity score (0.0-1.0)."""
    score = 0.3  # base
    score += min(sentence_count / 10, 0.4)  # up to 0.4 for sentence count
    score += min(len(text) / 1000, 0.2)  # up to 0.2 for length
    if any(kw in text.lower() for kw in ["complex", "difficult", "extensive"]):
        score += 0.1
    return min(score, 1.0)


# ── Step 2: DAG Build ────────────────────────────────────────────────────

def step_build_dag(
    composite_id: str,
    units: list[dict[str, Any]],
    dependencies: list[tuple[str, str]] | None = None,
) -> tuple[DAG, list[str]]:
    """Build a DAG from decomposed units.

    Returns (dag, errors).
    """
    errors: list[str] = []
    dependencies = dependencies or []

    dag = DAG(composite_id=composite_id)

    # Create nodes
    for i, u in enumerate(units):
        uid = u.get("id", _unit_id(composite_id, i))
        unit = Unit(
            id=uid,
            text=u.get("text", ""),
            type=u.get("type", "action"),
            estimated_duration=u.get("estimated_duration", 15),
        )
        dag.nodes[uid] = unit

    # Add edges
    for from_uid, to_uid in dependencies:
        if from_uid not in dag.nodes:
            errors.append(f"Dependency from unknown unit: {from_uid}")
            continue
        if to_uid not in dag.nodes:
            errors.append(f"Dependency to unknown unit: {to_uid}")
            continue
        if from_uid == to_uid:
            errors.append(f"Self-dependency: {from_uid}")
            continue
        dag.edges.append((from_uid, to_uid))
        dag.nodes[from_uid].dependents.append(to_uid)
        dag.nodes[to_uid].dependencies.append(from_uid)

    # Detect cycles
    dag.is_acyclic = not _detect_cycle(dag)

    if not dag.is_acyclic:
        errors.append("DAG contains cycles — cannot topologically sort")

    # Topological sort and assign levels
    if dag.is_acyclic:
        order = _topological_sort(dag)
        level_map: dict[str, int] = {}
        for nid in order:
            deps = dag.nodes[nid].dependencies
            if not deps:
                level_map[nid] = 0
            else:
                level_map[nid] = max(level_map.get(d, 0) for d in deps) + 1
            dag.nodes[nid].level = level_map[nid]

        if level_map:
            dag.total_levels = max(level_map.values()) + 1

    return dag, errors


# ── Step 3: Dependency Map ───────────────────────────────────────────────

def step_map_dependencies(
    units: list[dict[str, Any]],
    dependency_hints: list[str] | None = None,
) -> tuple[list[Dependency], list[str]]:
    """Map dependencies between units.

    Returns (dependencies, errors).
    """
    errors: list[str] = []
    dependencies: list[Dependency] = []

    if len(units) < 2:
        return [], []

    # Simple heuristic: sequential order implies dependency
    for i in range(len(units) - 1):
        from_uid = units[i].get("id", f"unit-{i}")
        to_uid = units[i + 1].get("id", f"unit-{i + 1}")
        dependencies.append(Dependency(
            from_unit=to_uid,  # to depends on from (sequential)
            to_unit=from_uid,
            type="sequential",
            strength="medium",
            rationale=f"Sequential order: {to_uid} follows {from_uid}",
        ))

    # Process dependency hints
    for hint in (dependency_hints or []):
        hint_lower = hint.lower()
        # Very basic hint parsing — look for "X before Y" or "Y after X"
        match = re.search(r"(\w+)\s+(?:before|after)\s+(\w+)", hint_lower)
        if match:
            a, b = match.group(1), match.group(2)
            # Find matching unit IDs
            for u in units:
                if a in u.get("text", "").lower() or a in u.get("id", "").lower():
                    for v in units:
                        if b in v.get("text", "").lower() or b in v.get("id", "").lower():
                            if u["id"] != v["id"]:
                                dependencies.append(Dependency(
                                    from_unit=v["id"],
                                    to_unit=u["id"],
                                    type="sequential",
                                    strength="strong",
                                    rationale=f"Hint: {hint}",
                                ))

    # Remove duplicates
    seen: set[tuple[str, str]] = set()
    unique_deps: list[Dependency] = []
    for dep in dependencies:
        key = (dep.from_unit, dep.to_unit)
        if key not in seen:
            seen.add(key)
            unique_deps.append(dep)

    return unique_deps, errors


# ── Step 4: Execution Order ──────────────────────────────────────────────

def step_execution_order(
    dag: DAG,
    parallelizable: bool = True,
    max_parallel: int = 3,
) -> tuple[ExecutionPlan, list[str]]:
    """Determine execution order from a DAG.

    Returns (plan, errors).
    """
    errors: list[str] = []

    if not dag.is_acyclic:
        errors.append("Cannot compute execution order for cyclic DAG")
        return ExecutionPlan(), errors

    if not dag.nodes:
        return ExecutionPlan(), errors

    # Topological sort
    order = _topological_sort(dag)

    # Compute levels
    level_map: dict[str, int] = {}
    for nid in order:
        deps = dag.nodes[nid].dependencies
        if not deps:
            level_map[nid] = 0
        else:
            level_map[nid] = max(level_map.get(d, 0) for d in deps) + 1

    max_level = max(level_map.values()) if level_map else 0

    # Group into waves
    waves: dict[int, list[str]] = {}
    for nid, level in level_map.items():
        waves.setdefault(level, []).append(nid)

    execution_waves: list[ExecutionWave] = []
    critical_path: list[str] = []
    total_duration = 0

    # Find critical path (longest chain)
    # Simple approach: for each leaf, trace back to root, find longest
    leaves = [nid for nid, n in dag.nodes.items() if not n.dependents]
    if leaves:
        best_path: list[str] = []
        best_duration = 0
        for leaf in leaves:
            path = _trace_back(leaf, dag, level_map)
            path_duration = sum(dag.nodes[nid].estimated_duration for nid in path)
            if path_duration > best_duration:
                best_duration = path_duration
                best_path = path
        critical_path = best_path
        total_duration = best_duration

    for level in sorted(waves.keys()):
        units_in_wave = waves[level]
        wave_duration = max(dag.nodes[uid].estimated_duration for uid in units_in_wave)
        execution_waves.append(ExecutionWave(
            wave=level,
            units=sorted(units_in_wave),
            estimated_wave_duration=wave_duration,
        ))

    # Count parallelizable units
    parallelizable_count = 0
    if parallelizable:
        for wave in execution_waves:
            if len(wave.units) > 1:
                parallelizable_count += len(wave.units)

    plan = ExecutionPlan(
        waves=execution_waves,
        critical_path=critical_path,
        total_estimated_duration=total_duration,
        total_waves=len(execution_waves),
        parallelizable_units=parallelizable_count,
    )

    return plan, errors


def _trace_back(
    start_nid: str,
    dag: DAG,
    level_map: dict[str, int],
) -> list[str]:
    """Trace back from a leaf to root, building the longest path."""
    path = [start_nid]
    current = start_nid

    while True:
        deps = dag.nodes[current].dependencies
        if not deps:
            break
        # Pick the dependency with the highest level (longest path)
        current = max(deps, key=lambda d: level_map.get(d, 0))
        path.append(current)

    path.reverse()
    return path


# ── S5 Decompose Agent ───────────────────────────────────────────────────

class S5Decompose:
    """S5 Decompose agent — Composites → DAGs.

    Detects composites, decomposes into units, maps dependencies,
    builds DAGs, and determines execution order.
    """

    def __init__(self, vault_path: str | None = None):
        self.vault_path = Path(vault_path) if vault_path else None
        self._composites: dict[str, Composite] = {}
        self._dags: dict[str, DAG] = {}
        self._plans: dict[str, ExecutionPlan] = {}

    # ── Detect ─────────────────────────────────────────────────────

    def detect_composites(
        self,
        content: str,
        min_size: int = 100,
        apply: bool = False,
    ) -> dict[str, Any]:
        """Detect composite tasks from content."""
        composites, errors = step_detect_composites(content, min_size)
        for c in composites:
            self._composites[c.id] = c
        if apply:
            self.save_to_vault(apply=True)
        return {
            "composites": [c.to_dict() for c in composites],
            "total": len(composites),
            "ok": len(errors) == 0,
            "errors": errors,
        }

    # ── Decompose ──────────────────────────────────────────────────

    def decompose(
        self,
        composite_id: str,
        units_data: list[dict[str, Any]] | None = None,
        dependencies: list[tuple[str, str]] | None = None,
    ) -> dict[str, Any]:
        """Decompose a composite into units and build a DAG."""
        if composite_id not in self._composites:
            return {
                "composite_id": composite_id,
                "dag": None,
                "ok": False,
                "errors": [f"Composite not found: {composite_id}"],
            }

        composite = self._composites[composite_id]

        # If no units provided, auto-decompose the composite text
        if units_data is None:
            unit_texts = _split_into_units(composite.text)
            units_data = []
            for i, ut in enumerate(unit_texts):
                units_data.append({
                    "id": _unit_id(composite_id, i),
                    "text": ut,
                    "type": _classify_unit_type(ut),
                    "estimated_duration": _estimate_duration(ut),
                })

        # Map dependencies if not provided
        if dependencies is None:
            deps, _ = step_map_dependencies(units_data)
            dependencies = [(d.from_unit, d.to_unit) for d in deps]

        dag, errors = step_build_dag(composite_id, units_data, dependencies)
        self._dags[composite_id] = dag

        return {
            "composite_id": composite_id,
            "dag": dag.to_dict(),
            "ok": len(errors) == 0,
            "errors": errors,
        }

    # ── Execution Order ────────────────────────────────────────────

    def execution_order(
        self,
        composite_id: str,
        parallelizable: bool = True,
        max_parallel: int = 3,
        apply: bool = False,
    ) -> dict[str, Any]:
        """Determine execution order from a composite's DAG."""
        if composite_id not in self._dags:
            return {
                "composite_id": composite_id,
                "plan": None,
                "ok": False,
                "errors": [f"No DAG found for composite: {composite_id}"],
            }

        dag = self._dags[composite_id]
        plan, errors = step_execution_order(dag, parallelizable, max_parallel)
        self._plans[composite_id] = plan
        if apply:
            self.save_to_vault(apply=True)

        return {
            "composite_id": composite_id,
            "plan": plan.to_dict(),
            "ok": len(errors) == 0,
            "errors": errors,
        }

    # ── Stats ──────────────────────────────────────────────────────

    def stats(self) -> dict[str, Any]:
        """Decompose statistics."""
        total_units = sum(len(dag.nodes) for dag in self._dags.values())
        total_edges = sum(len(dag.edges) for dag in self._dags.values())
        acyclic_count = sum(1 for dag in self._dags.values() if dag.is_acyclic)
        return {
            "total_composites": len(self._composites),
            "total_dags": len(self._dags),
            "total_units": total_units,
            "total_edges": total_edges,
            "acyclic_dags": acyclic_count,
            "total_plans": len(self._plans),
        }

    # ── Persistence ────────────────────────────────────────────────

    def save_to_vault(self, apply: bool = False) -> str | None:
        """Save decompose data to vault as JSON (if --apply / vault configured)."""
        if not self.vault_path or not apply:
            return None

        dir_path = self.vault_path / "02-Areas" / "Skills"
        dir_path.mkdir(parents=True, exist_ok=True)

        data = {
            "composites": {cid: c.to_dict() for cid, c in self._composites.items()},
            "dags": {cid: dag.to_dict() for cid, dag in self._dags.items()},
            "plans": {cid: plan.to_dict() for cid, plan in self._plans.items()},
            "stats": self.stats(),
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }

        path = dir_path / "decompose-dags.json"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return str(path)

    def load_from_vault(self) -> bool:
        """Load decompose data from vault JSON file."""
        if not self.vault_path:
            return False

        path = self.vault_path / "02-Areas" / "Skills" / "decompose-dags.json"
        if not path.exists():
            return False

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for cid, cdata in data.get("composites", {}).items():
                self._composites[cid] = Composite(**cdata)
            for cid, ddata in data.get("dags", {}).items():
                dag = DAG(composite_id=cid)
                for nid, ndata in ddata.get("nodes", {}).items():
                    dag.nodes[nid] = Unit(**ndata)
                dag.edges = [(e["from"], e["to"]) for e in ddata.get("edges", [])]
                dag.is_acyclic = ddata.get("is_acyclic", True)
                dag.total_levels = ddata.get("total_levels", 0)
                self._dags[cid] = dag
            for cid, pdata in data.get("plans", {}).items():
                waves = [
                    ExecutionWave(
                        wave=w["wave"],
                        units=w["units"],
                        estimated_wave_duration=w["estimated_wave_duration"],
                    )
                    for w in pdata.get("execution_order", [])
                ]
                self._plans[cid] = ExecutionPlan(
                    waves=waves,
                    critical_path=pdata.get("critical_path", []),
                    total_estimated_duration=pdata.get("total_estimated_duration", 0),
                    total_waves=pdata.get("total_waves", 0),
                    parallelizable_units=pdata.get("parallelizable_units", 0),
                )
            return True
        except (json.JSONDecodeError, TypeError, KeyError):
            return False


# ── CLI ──────────────────────────────────────────────────────────────────

import argparse  # noqa: E402
import sys  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Borg S5 Decompose — Composites → DAGs",
    )
    parser.add_argument("--vault", required=True, help="Path to vault directory")

    sub = parser.add_subparsers(dest="command")

    # detect
    p_detect = sub.add_parser("detect", help="Detect composite tasks from content")
    p_detect.add_argument("--content", required=True, help="Content to analyze")
    p_detect.add_argument(
        "--min-size", type=int, default=100, help="Minimum composite size"
    )

    # decompose
    p_decompose = sub.add_parser(
        "decompose", help="Decompose a composite into units and build DAG"
    )
    p_decompose.add_argument(
        "--composite-id", required=True, help="Composite ID to decompose"
    )
    p_decompose.add_argument(
        "--units-json", help="JSON file with units list"
    )
    p_decompose.add_argument(
        "--deps-json", help="JSON file with dependency pairs list"
    )

    # execution-order
    p_order = sub.add_parser(
        "execution-order", help="Determine execution order from DAG"
    )
    p_order.add_argument(
        "--composite-id", required=True, help="Composite ID"
    )
    p_order.add_argument(
        "--parallelizable",
        action="store_true",
        default=True,
        help="Identify parallelizable units",
    )
    p_order.add_argument(
        "--max-parallel", type=int, default=3, help="Max parallel units per wave"
    )

    # stats
    sub.add_parser("stats", help="Show decompose statistics")

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
    print("Borg S5 Decompose — Self-Test Suite")
    print("=" * 50)

    passed = 0
    failed = 0

    # Test 1: Detect composites
    print("\n[1/7] Detect composites...")
    decompose = S5Decompose()
    result = decompose.detect_composites(
        "First, we need to research the market. Then, analyze the competitors. "
        "After that, build the implementation plan. Finally, deploy to production."
    )
    assert result["ok"], f"Detect failed: {result['errors']}"
    assert result["total"] > 0, "Should detect at least one composite"
    print(f"  ✅ Detected {result['total']} composites")
    passed += 1

    # Test 2: Decompose with units
    print("\n[2/7] Decompose...")
    composites = result["composites"]
    if composites:
        cid = composites[0]["id"]
        units = [
            {"id": "u1", "text": "Research the market", "type": "research", "estimated_duration": 30},
            {"id": "u2", "text": "Analyze competitors", "type": "analysis", "estimated_duration": 20},
            {"id": "u3", "text": "Build implementation plan", "type": "action", "estimated_duration": 45},
        ]
        deps = [("u2", "u1"), ("u3", "u2")]
        result2 = decompose.decompose(cid, units, deps)
        assert result2["ok"], f"Decompose failed: {result2['errors']}"
        assert result2["dag"]["is_acyclic"], "DAG should be acyclic"
        print(f"  ✅ Decomposed: {len(result2['dag']['nodes'])} nodes, {len(result2['dag']['edges'])} edges")
        passed += 1
    else:
        print("  ⚠️  Skipped (no composites detected)")
        passed += 1

    # Test 3: Execution order
    print("\n[3/7] Execution order...")
    if composites:
        cid = composites[0]["id"]
        result3 = decompose.execution_order(cid)
        assert result3["ok"], f"Execution order failed: {result3['errors']}"
        plan = result3["plan"]
        assert plan["total_waves"] >= 1, "Should have at least one wave"
        print(f"  ✅ Execution order: {plan['total_waves']} waves, {plan['total_estimated_duration']} min total")
        passed += 1
    else:
        print("  ⚠️  Skipped (no composites detected)")
        passed += 1

    # Test 4: Auto-decompose (no units provided)
    print("\n[4/7] Auto-decompose...")
    result4 = decompose.detect_composites(
        "Set up the development environment. Configure the database. Run the tests."
    )
    assert result4["ok"], f"Auto-detect failed: {result4['errors']}"
    if result4["composites"]:
        cid2 = result4["composites"][0]["id"]
        result5 = decompose.decompose(cid2)
        assert result5["ok"], f"Auto-decompose failed: {result5['errors']}"
        print(f"  ✅ Auto-decomposed: {len(result5['dag']['nodes'])} units")
        passed += 1
    else:
        print("  ⚠️  Skipped (no composites detected)")
        passed += 1

    # Test 5: Stats
    print("\n[5/7] Stats...")
    stats = decompose.stats()
    assert stats["total_composites"] >= 1
    assert stats["total_dags"] >= 1
    print(f"  ✅ Stats: {stats['total_composites']} composites, {stats['total_dags']} DAGs, {stats['total_units']} units")
    passed += 1

    # Test 6: Cycle detection
    print("\n[6/7] Cycle detection...")
    result6 = decompose.detect_composites("Step A then step B then step C then back to A.")
    assert result6["ok"], f"Cycle detect failed: {result6['errors']}"
    print(f"  ✅ Cycle detection: {result6['total']} composites detected")
    passed += 1

    # Test 7: Empty content
    print("\n[7/7] Empty content...")
    result7 = decompose.detect_composites("")
    assert not result7["ok"], "Empty content should fail"
    assert result7["errors"], "Should have errors"
    print(f"  ✅ Empty content correctly rejected: {result7['errors'][0]}")
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

    decompose = S5Decompose(vault_path=args.vault)
    decompose.load_from_vault()

    dry_run = args.dry_run and not args.apply

    if args.command == "detect":
        result = decompose.detect_composites(
            args.content,
            min_size=args.min_size,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    if args.command == "decompose":
        units_data = None
        if args.units_json:
            with open(args.units_json) as f:
                units_data = json.load(f)
        deps = None
        if args.deps_json:
            with open(args.deps_json) as f:
                deps_data = json.load(f)
                if isinstance(deps_data, list):
                    deps = [tuple(d) for d in deps_data]
        result = decompose.decompose(
            args.composite_id,
            units_data,
            deps,
        )
        print(json.dumps(result, indent=2))
        if result["ok"] and not dry_run:
            path = decompose.save_to_vault(apply=True)
            if path:
                print(f"\nSaved to: {path}")
        return 0 if result["ok"] else 1

    if args.command == "execution-order":
        result = decompose.execution_order(
            args.composite_id,
            parallelizable=args.parallelizable,
            max_parallel=args.max_parallel,
        )
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    if args.command == "stats":
        stats = decompose.stats()
        print(json.dumps(stats, indent=2))
        return 0

    print("No action given. Run with --help to see the options.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
