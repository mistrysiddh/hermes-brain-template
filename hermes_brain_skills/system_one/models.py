"""System One Memory OS — Section 4: Canonical Data Model.

Record types from mem-draft-spec.txt §4:
- source: Origin + trust boundary
- artifact: Immutable source version
- observation: Atomic memory unit
- memory_type: Overlapping multi-label
- entity: Canonical referent
- mention: Occurrence mapping
- edge: Derived multi-view relation
- version_relation: Continuity & evolution
- summary: Derived representation only
- procedure: Executable skill / template / framework
- decision_trace: System One audit
- query_trace: Retrieval audit
- feedback: Human correction
- scope: Multi-agent partitioning
- semantic_cache: O(1) intercept
- agent_task: Deterministic coordination
- access_index: Evolving retrieval weights
- mental_model: Framework instance
- skill_library_entry: Portable induced capability

All records use the schema ⟨M,R,C,P,T,N,X,E,D⟩:
- M: metadata (record kind, version, timestamps)
- R: record ID (content-hash or UUID)
- C: content (the actual payload)
- P: provenance (source, captured_by, captured_at)
- T: type (record kind + sub-type)
- N: name / label (human-readable)
- X: extensions (arbitrary key-value)
- E: edges (relations to other records)
- D: derived (computed fields, embeddings, access weights)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import hashlib
import json
import uuid


# ── Record kinds ──────────────────────────────────────────────────────────

class RecordKind(str, Enum):
    SOURCE = "source"
    ARTIFACT = "artifact"
    OBSERVATION = "observation"
    MEMORY_TYPE = "memory_type"
    ENTITY = "entity"
    MENTION = "mention"
    EDGE = "edge"
    VERSION_RELATION = "version_relation"
    SUMMARY = "summary"
    PROCEDURE = "procedure"
    DECISION_TRACE = "decision_trace"
    QUERY_TRACE = "query_trace"
    FEEDBACK = "feedback"
    SCOPE = "scope"
    SEMANTIC_CACHE = "semantic_cache"
    AGENT_TASK = "agent_task"
    ACCESS_INDEX = "access_index"
    MENTAL_MODEL = "mental_model"
    SKILL_LIBRARY_ENTRY = "skill_library_entry"


# ── Memory types (overlapping multi-label) ───────────────────────────────

MEMORY_TYPES = [
    "episodic", "semantic", "procedural", "preference",
    "decision", "commitment", "open-loop", "gotcha",
    "convention", "task", "contact", "reference",
    "framework", "skill",
]

# ── Edge view types ───────────────────────────────────────────────────────

EDGE_VIEW_TYPES = [
    "semantic", "temporal", "causal", "entity",
    "structural", "lateral", "perspective",
]

# ── Edge subtypes ─────────────────────────────────────────────────────────

DETERMINISTIC_EDGE_SUBTYPES = [
    "PRECEDES", "MENTIONS", "DEFINED_IN", "CALLS", "IMPORTS",
    "CHANGED_BY", "BELONGS_TO",
]

MODEL_JUDGED_EDGE_SUBTYPES = [
    "SEMANTICALLY_RELATED", "CAUSES", "CAUSED_BY", "ENABLES",
    "PREVENTS", "SAME_ENTITY", "RESPONDS_TO", "REVISES",
    "ANALOGOUS_TO", "REFRAMES", "PERSPECTIVE_OF", "GENERALIZES",
]

# ── Version relations ─────────────────────────────────────────────────────

VERSION_RELATIONS = [
    "duplicates", "supersedes", "contradicts", "corrects",
    "subsumes", "reframes", "generalizes",
]


# ── Record schema ⟨M,R,C,P,T,N,X,E,D⟩ ─────────────────────────────────────

@dataclass
class Record:
    """Base record with schema ⟨M,R,C,P,T,N,X,E,D⟩."""

    # M: metadata
    record_kind: RecordKind
    version: str = "1.0"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # R: record ID (content-hash or UUID)
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # C: content (the actual payload)
    content: dict[str, Any] = field(default_factory=dict)

    # P: provenance
    provenance: dict[str, Any] = field(default_factory=dict)

    # T: type
    record_type: str = ""
    sub_type: str = ""

    # N: name / label
    name: str = ""

    # X: extensions (arbitrary key-value)
    extensions: dict[str, Any] = field(default_factory=dict)

    # E: edges (relations to other records)
    edges: list[dict[str, Any]] = field(default_factory=list)

    # D: derived (computed fields, embeddings, access weights)
    derived: dict[str, Any] = field(default_factory=dict)

    def content_hash(self) -> str:
        """SHA-256 content hash for immutable addressing."""
        payload = json.dumps({
            "kind": self.record_kind.value,
            "type": self.record_type,
            "sub_type": self.sub_type,
            "name": self.name,
            "content": self.content,
            "provenance": self.provenance,
            "extensions": self.extensions,
        }, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def to_dict(self) -> dict[str, Any]:
        return {
            "M": {
                "record_kind": self.record_kind.value,
                "version": self.version,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            },
            "R": self.record_id,
            "C": self.content,
            "P": self.provenance,
            "T": {
                "record_type": self.record_type,
                "sub_type": self.sub_type,
            },
            "N": self.name,
            "X": self.extensions,
            "E": self.edges,
            "D": self.derived,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Record":
        m = data.get("M", {})
        t = data.get("T", {})
        return cls(
            record_kind=RecordKind(m.get("record_kind", "observation")),
            version=m.get("version", "1.0"),
            created_at=m.get("created_at", ""),
            updated_at=m.get("updated_at", ""),
            record_id=data.get("R", str(uuid.uuid4())),
            content=data.get("C", {}),
            provenance=data.get("P", {}),
            record_type=t.get("record_type", ""),
            sub_type=t.get("sub_type", ""),
            name=data.get("N", ""),
            extensions=data.get("X", {}),
            edges=data.get("E", []),
            derived=data.get("D", {}),
        )


# ── Specific record types ─────────────────────────────────────────────────

@dataclass
class SourceRecord(Record):
    """source: Origin + trust boundary."""
    def __init__(self, **kwargs: Any):
        kwargs.setdefault("record_kind", RecordKind.SOURCE)
        super().__init__(**kwargs)


@dataclass
class ArtifactRecord(Record):
    """artifact: Immutable source version."""
    def __init__(self, **kwargs: Any):
        kwargs.setdefault("record_kind", RecordKind.ARTIFACT)
        super().__init__(**kwargs)


@dataclass
class ObservationRecord(Record):
    """observation: Atomic memory unit."""
    def __init__(self, **kwargs: Any):
        kwargs.setdefault("record_kind", RecordKind.OBSERVATION)
        super().__init__(**kwargs)


@dataclass
class EntityRecord(Record):
    """entity: Canonical referent."""
    def __init__(self, **kwargs: Any):
        kwargs.setdefault("record_kind", RecordKind.ENTITY)
        super().__init__(**kwargs)


@dataclass
class EdgeRecord(Record):
    """edge: Derived multi-view relation."""
    def __init__(self, **kwargs: Any):
        kwargs.setdefault("record_kind", RecordKind.EDGE)
        super().__init__(**kwargs)


@dataclass
class VersionRelationRecord(Record):
    """version_relation: Continuity & evolution."""
    def __init__(self, **kwargs: Any):
        kwargs.setdefault("record_kind", RecordKind.VERSION_RELATION)
        super().__init__(**kwargs)


@dataclass
class ProcedureRecord(Record):
    """procedure: Executable skill / template / framework."""
    def __init__(self, **kwargs: Any):
        kwargs.setdefault("record_kind", RecordKind.PROCEDURE)
        super().__init__(**kwargs)


@dataclass
class DecisionTraceRecord(Record):
    """decision_trace: System One audit."""
    def __init__(self, **kwargs: Any):
        kwargs.setdefault("record_kind", RecordKind.DECISION_TRACE)
        super().__init__(**kwargs)


@dataclass
class MentalModelRecord(Record):
    """mental_model: Framework instance."""
    def __init__(self, **kwargs: Any):
        kwargs.setdefault("record_kind", RecordKind.MENTAL_MODEL)
        super().__init__(**kwargs)


@dataclass
class SkillLibraryEntryRecord(Record):
    """skill_library_entry: Portable induced capability."""
    def __init__(self, **kwargs: Any):
        kwargs.setdefault("record_kind", RecordKind.SKILL_LIBRARY_ENTRY)
        super().__init__(**kwargs)


# ── Record factory ────────────────────────────────────────────────────────

RECORD_CLASSES: dict[RecordKind, type[Record]] = {
    RecordKind.SOURCE: SourceRecord,
    RecordKind.ARTIFACT: ArtifactRecord,
    RecordKind.OBSERVATION: ObservationRecord,
    RecordKind.MEMORY_TYPE: Record,
    RecordKind.ENTITY: EntityRecord,
    RecordKind.MENTION: Record,
    RecordKind.EDGE: EdgeRecord,
    RecordKind.VERSION_RELATION: VersionRelationRecord,
    RecordKind.SUMMARY: Record,
    RecordKind.PROCEDURE: ProcedureRecord,
    RecordKind.DECISION_TRACE: DecisionTraceRecord,
    RecordKind.QUERY_TRACE: Record,
    RecordKind.FEEDBACK: Record,
    RecordKind.SCOPE: Record,
    RecordKind.SEMANTIC_CACHE: Record,
    RecordKind.AGENT_TASK: Record,
    RecordKind.ACCESS_INDEX: Record,
    RecordKind.MENTAL_MODEL: MentalModelRecord,
    RecordKind.SKILL_LIBRARY_ENTRY: SkillLibraryEntryRecord,
}


def create_record(kind: RecordKind | str, **kwargs: Any) -> Record:
    """Factory to create a record of the given kind."""
    if isinstance(kind, str):
        kind = RecordKind(kind)
    cls = RECORD_CLASSES.get(kind, Record)
    return cls(**kwargs)


def record_to_json(record: Record) -> str:
    """Serialize a record to JSON."""
    return json.dumps(record.to_dict(), sort_keys=True, separators=(",", ":"))


def record_from_json(data: str) -> Record:
    """Deserialize a record from JSON."""
    return Record.from_dict(json.loads(data))
