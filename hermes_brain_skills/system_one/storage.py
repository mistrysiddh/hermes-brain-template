"""System One Memory OS — Section 3: Storage Architecture.

Canonical Store per mem-draft-spec.txt §3:
- Single portable file per privacy/workspace boundary
- WAL mode enabling concurrent multi-agent read/write
- Dual FTS: unicode (natural language) + trigram (code/paths/IDs)
- Ordinary tables for adjacency, temporal validity, entities, traces, tasks,
  cache, access indexes, framework instances, skill library
- Content-hash integrity on every artifact
- O(1) semantic cache table with TTL
"""

from __future__ import annotations

import sqlite3
import json
import os
import hashlib
import time
from datetime import datetime, timezone
from typing import Any

from hermes_brain_skills.system_one.models import (
    Record, RecordKind, create_record, record_to_json, record_from_json,
    EDGE_VIEW_TYPES, MODEL_JUDGED_EDGE_SUBTYPES, DETERMINISTIC_EDGE_SUBTYPES,
    VERSION_RELATIONS, MEMORY_TYPES,
)


class CanonicalStore:
    """Single-file SQLite WAL store per privacy/workspace boundary.

    Implements Section 3 Canonical Store checklist:
    - WAL mode for concurrent multi-agent read/write
    - Content-hash integrity on every artifact
    - Dual FTS (unicode + trigram)
    - Ordinary tables for adjacency, temporal validity, entities, traces,
      tasks, cache, access indexes, framework instances, skill library
    - O(1) semantic cache with TTL
    """

    def __init__(self, path: str, read_only: bool = False):
        self.path = path
        self.read_only = read_only
        self._conn: sqlite3.Connection | None = None
        self._init_db()

    def _init_db(self) -> None:
        mode = "ro" if self.read_only else "rwc"
        uri = f"file:{self.path}?mode={mode}"
        self._conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables()

    def _create_tables(self) -> None:
        c = self._conn.cursor()

        # ── artifacts ── immutable source versions with content-hash integrity
        c.execute("""
            CREATE TABLE IF NOT EXISTS artifacts (
                record_id TEXT PRIMARY KEY,
                content_hash TEXT NOT NULL UNIQUE,
                mime_type TEXT,
                source_version TEXT,
                captured_at TEXT NOT NULL,
                raw_uri TEXT,
                size INTEGER,
                json_payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # ── observations ── atomic memory units
        c.execute("""
            CREATE TABLE IF NOT EXISTS observations (
                record_id TEXT PRIMARY KEY,
                artifact_id TEXT,
                text TEXT NOT NULL,
                source_span TEXT,
                status TEXT DEFAULT 'active',
                embedding_ref TEXT,
                json_payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (artifact_id) REFERENCES artifacts(record_id)
            )
        """)

        # ── entities ── canonical referents
        c.execute("""
            CREATE TABLE IF NOT EXISTS entities (
                record_id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                name TEXT NOT NULL,
                aliases TEXT,  -- JSON array
                identifiers TEXT,  -- JSON array
                current_facts TEXT,  -- JSON
                json_payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # ── edges ── derived multi-view relations
        c.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                record_id TEXT PRIMARY KEY,
                view TEXT NOT NULL,
                subtype TEXT NOT NULL,
                direction TEXT NOT NULL,
                confidence REAL NOT NULL,
                provenance TEXT NOT NULL,  -- JSON
                validity_from TEXT,
                validity_to TEXT,
                decision_trace_id TEXT,
                json_payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # ── version_relations ── continuity & evolution
        c.execute("""
            CREATE TABLE IF NOT EXISTS version_relations (
                record_id TEXT PRIMARY KEY,
                relation_type TEXT NOT NULL,
                from_record_id TEXT NOT NULL,
                to_record_id TEXT NOT NULL,
                json_payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # ── summaries ── derived representations
        c.execute("""
            CREATE TABLE IF NOT EXISTS summaries (
                record_id TEXT PRIMARY KEY,
                source_observation_ids TEXT NOT NULL,  -- JSON array
                model TEXT NOT NULL,
                version TEXT NOT NULL,
                created_at TEXT NOT NULL,
                json_payload TEXT NOT NULL
            )
        """)

        # ── procedures ── executable skill / template / framework
        c.execute("""
            CREATE TABLE IF NOT EXISTS procedures (
                record_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                ordered_steps TEXT NOT NULL,  -- JSON array
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                applicable_contexts TEXT,  -- JSON
                linked_observations TEXT,  -- JSON array
                utility REAL DEFAULT 0.0,
                framework_type TEXT,
                version TEXT,
                json_payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # ── decision_traces ── System One audit
        c.execute("""
            CREATE TABLE IF NOT EXISTS decision_traces (
                record_id TEXT PRIMARY KEY,
                schema_id TEXT NOT NULL,
                state_hash TEXT NOT NULL,
                full_distribution TEXT NOT NULL,  -- JSON
                model TEXT NOT NULL,
                checkpoint TEXT NOT NULL,
                latency_ms REAL NOT NULL,
                cache_hit INTEGER DEFAULT 0,
                calibration REAL,
                fallback TEXT,
                json_payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # ── agent_tasks ── deterministic coordination
        c.execute("""
            CREATE TABLE IF NOT EXISTS agent_tasks (
                task_id TEXT PRIMARY KEY,
                dependencies TEXT,  -- JSON array
                status TEXT NOT NULL DEFAULT 'pending',
                assigned_agent TEXT,
                evidence_id TEXT,
                locks TEXT,  -- JSON
                created_at TEXT NOT NULL
            )
        """)

        # ── access_index ── evolving retrieval weights
        c.execute("""
            CREATE TABLE IF NOT EXISTS access_index (
                memory_id TEXT PRIMARY KEY,
                keep_suppress TEXT NOT NULL DEFAULT 'keep',  -- keep/suppress
                frequency INTEGER DEFAULT 0,
                learned_utility REAL DEFAULT 0.0,
                updated_at TEXT NOT NULL
            )
        """)

        # ── mental_models ── framework instances
        c.execute("""
            CREATE TABLE IF NOT EXISTS mental_models (
                record_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                model_type TEXT NOT NULL,
                parameters TEXT,  -- JSON
                linked_procedures TEXT,  -- JSON array
                success_metrics TEXT,  -- JSON
                version TEXT,
                json_payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # ── skill_library_entries ── portable induced capabilities
        c.execute("""
            CREATE TABLE IF NOT EXISTS skill_library_entries (
                record_id TEXT PRIMARY KEY,
                procedure_id TEXT NOT NULL,
                export_format TEXT NOT NULL,
                compatibility TEXT,
                validation_status TEXT DEFAULT 'pending',
                json_payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # ── semantic_cache ── O(1) intercept with TTL
        c.execute("""
            CREATE TABLE IF NOT EXISTS semantic_cache (
                query_hash TEXT PRIMARY KEY,
                canonical_query TEXT NOT NULL,
                bundled_evidence_id TEXT NOT NULL,
                ttl INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL
            )
        """)

        # ── scopes ── multi-agent partitioning
        c.execute("""
            CREATE TABLE IF NOT EXISTS scopes (
                scope_id TEXT PRIMARY KEY,
                scope_type TEXT NOT NULL,  -- global/project:X/agent:Y/team:Z/org/session
                name TEXT NOT NULL,
                json_payload TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        # ── Dual FTS: unicode + trigram ──
        # Unicode FTS for natural language search
        c.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS fts_unicode USING fts5(
                record_id, text, content=observations, content_rowid=record_id
            )
        """)
        # Trigram FTS for code/paths/IDs (using simple trigram via SQLite)
        c.execute("""
            CREATE TABLE IF NOT EXISTS trigram_index (
                trigram TEXT NOT NULL,
                record_id TEXT NOT NULL,
                record_kind TEXT NOT NULL,
                PRIMARY KEY (trigram, record_id, record_kind)
            )
        """)

        # ── feedback ── human correction
        c.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                record_id TEXT PRIMARY KEY,
                observation_id TEXT NOT NULL,
                action TEXT NOT NULL,  -- accepted/rejected/edited/missing
                reason TEXT,
                user TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (observation_id) REFERENCES observations(record_id)
            )
        """)

        self._conn.commit()

    # ── Write operations ────────────────────────────────────────────────

    def write_record(self, record: Record) -> str:
        """Write a record to the canonical store. Returns record_id."""
        c = self._conn.cursor()
        now = datetime.now(timezone.utc).isoformat()
        json_payload = record_to_json(record)

        kind = record.record_kind
        if kind == RecordKind.ARTIFACT:
            content_hash = record.content_hash()
            c.execute(
                """INSERT OR REPLACE INTO artifacts
                   (record_id, content_hash, mime_type, source_version,
                    captured_at, raw_uri, size, json_payload, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.record_id, content_hash,
                    record.content.get("mime_type", ""),
                    record.provenance.get("source_version", ""),
                    record.provenance.get("captured_at", now),
                    record.content.get("raw_uri", ""),
                    len(json_payload),
                    json_payload, now,
                ),
            )
        elif kind == RecordKind.OBSERVATION:
            artifact_id = record.content.get("artifact_id", "") or None
            c.execute(
                """INSERT OR REPLACE INTO observations
                   (record_id, artifact_id, text, source_span, status,
                    embedding_ref, json_payload, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.record_id,
                    artifact_id,
                    record.content.get("text", ""),
                    record.content.get("source_span", ""),
                    record.content.get("status", "active"),
                    record.derived.get("embedding_ref", ""),
                    json_payload, now,
                ),
            )
            # Index in FTS
            c.execute(
                "INSERT OR REPLACE INTO fts_unicode(record_id, text) VALUES (?, ?)",
                (record.record_id, record.content.get("text", "")),
            )
            # Trigram index
            self._update_trigram_index(c, record.record_id, kind.value,
                                       record.content.get("text", ""))
        elif kind == RecordKind.ENTITY:
            c.execute(
                """INSERT OR REPLACE INTO entities
                   (record_id, entity_type, name, aliases, identifiers,
                    current_facts, json_payload, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.record_id,
                    record.content.get("type", ""),
                    record.name,
                    json.dumps(record.content.get("aliases", [])),
                    json.dumps(record.content.get("identifiers", [])),
                    json.dumps(record.content.get("current_facts", {})),
                    json_payload, now,
                ),
            )
        elif kind == RecordKind.EDGE:
            c.execute(
                """INSERT OR REPLACE INTO edges
                   (record_id, view, subtype, direction, confidence,
                    provenance, validity_from, validity_to,
                    decision_trace_id, json_payload, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.record_id,
                    record.content.get("view", "semantic"),
                    record.content.get("subtype", "SEMANTICALLY_RELATED"),
                    record.content.get("direction", "out"),
                    float(record.content.get("confidence", 1.0)),
                    json.dumps(record.provenance),
                    record.content.get("validity_from", ""),
                    record.content.get("validity_to", ""),
                    record.content.get("decision_trace_id", ""),
                    json_payload, now,
                ),
            )
        elif kind == RecordKind.VERSION_RELATION:
            c.execute(
                """INSERT OR REPLACE INTO version_relations
                   (record_id, relation_type, from_record_id, to_record_id,
                    json_payload, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    record.record_id,
                    record.content.get("relation_type", ""),
                    record.content.get("from_record_id", ""),
                    record.content.get("to_record_id", ""),
                    json_payload, now,
                ),
            )
        elif kind == RecordKind.PROCEDURE:
            c.execute(
                """INSERT OR REPLACE INTO procedures
                   (record_id, name, ordered_steps, success_count,
                    failure_count, applicable_contexts, linked_observations,
                    utility, framework_type, version, json_payload, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.record_id,
                    record.name,
                    json.dumps(record.content.get("ordered_steps", [])),
                    record.content.get("success_count", 0),
                    record.content.get("failure_count", 0),
                    json.dumps(record.content.get("applicable_contexts", [])),
                    json.dumps(record.content.get("linked_observations", [])),
                    float(record.content.get("utility", 0.0)),
                    record.content.get("framework_type", ""),
                    record.content.get("version", ""),
                    json_payload, now,
                ),
            )
        elif kind == RecordKind.DECISION_TRACE:
            c.execute(
                """INSERT OR REPLACE INTO decision_traces
                   (record_id, schema_id, state_hash, full_distribution,
                    model, checkpoint, latency_ms, cache_hit, calibration,
                    fallback, json_payload, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.record_id,
                    record.content.get("schema_id", ""),
                    record.content.get("state_hash", ""),
                    json.dumps(record.derived.get("full_distribution", {})),
                    record.content.get("model", ""),
                    record.content.get("checkpoint", ""),
                    float(record.content.get("latency_ms", 0.0)),
                    int(record.content.get("cache_hit", 0)),
                    record.content.get("calibration"),
                    record.content.get("fallback"),
                    json_payload, now,
                ),
            )
        elif kind == RecordKind.AGENT_TASK:
            c.execute(
                """INSERT OR REPLACE INTO agent_tasks
                   (task_id, dependencies, status, assigned_agent,
                    evidence_id, locks, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.record_id,
                    json.dumps(record.content.get("dependencies", [])),
                    record.content.get("status", "pending"),
                    record.content.get("assigned_agent", ""),
                    record.content.get("evidence_id", ""),
                    json.dumps(record.content.get("locks", [])),
                    now,
                ),
            )
        elif kind == RecordKind.ACCESS_INDEX:
            c.execute(
                """INSERT OR REPLACE INTO access_index
                   (memory_id, keep_suppress, frequency, learned_utility, updated_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    record.record_id,
                    record.content.get("keep_suppress", "keep"),
                    int(record.content.get("frequency", 0)),
                    float(record.content.get("learned_utility", 0.0)),
                    now,
                ),
            )
        elif kind == RecordKind.MENTAL_MODEL:
            c.execute(
                """INSERT OR REPLACE INTO mental_models
                   (record_id, name, model_type, parameters, linked_procedures,
                    success_metrics, version, json_payload, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.record_id,
                    record.name,
                    record.content.get("model_type", ""),
                    json.dumps(record.content.get("parameters", {})),
                    json.dumps(record.content.get("linked_procedures", [])),
                    json.dumps(record.content.get("success_metrics", {})),
                    record.content.get("version", ""),
                    json_payload, now,
                ),
            )
        elif kind == RecordKind.SKILL_LIBRARY_ENTRY:
            c.execute(
                """INSERT OR REPLACE INTO skill_library_entries
                   (record_id, procedure_id, export_format, compatibility,
                    validation_status, json_payload, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.record_id,
                    record.content.get("procedure_id", ""),
                    record.content.get("export_format", ""),
                    record.content.get("compatibility", ""),
                    record.content.get("validation_status", "pending"),
                    json_payload, now,
                ),
            )
        else:
            # Generic record — store in a catch-all
            c.execute(
                """INSERT OR REPLACE INTO observations
                   (record_id, artifact_id, text, source_span, status,
                    embedding_ref, json_payload, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.record_id, "",
                    json.dumps(record.content), "",
                    "active", "", json_payload, now,
                ),
            )

        self._conn.commit()
        return record.record_id

    def _update_trigram_index(self, c: sqlite3.Cursor, record_id: str,
                              kind: str, text: str) -> None:
        """Index text trigrams for code/path/ID search."""
        if not text:
            return
        # Remove old entries
        c.execute("DELETE FROM trigram_index WHERE record_id = ?", (record_id,))
        # Generate trigrams
        for i in range(len(text) - 2):
            tri = text[i:i + 3]
            c.execute(
                "INSERT OR IGNORE INTO trigram_index(trigram, record_id, record_kind) VALUES (?, ?, ?)",
                (tri, record_id, kind),
            )

    # ── Read operations ─────────────────────────────────────────────────

    def read_record(self, record_id: str) -> Record | None:
        """Read a record by ID. Tries all tables."""
        c = self._conn.cursor()
        tables = [
            "artifacts", "observations", "entities", "edges",
            "version_relations", "summaries", "procedures",
            "decision_traces", "agent_tasks", "access_index",
            "mental_models", "skill_library_entries",
        ]
        for table in tables:
            c.execute(f"SELECT json_payload FROM {table} WHERE record_id = ?", (record_id,))
            row = c.fetchone()
            if row:
                return record_from_json(row[0])
        return None

    def read_artifact(self, record_id: str) -> dict[str, Any] | None:
        c = self._conn.cursor()
        c.execute("SELECT json_payload FROM artifacts WHERE record_id = ?", (record_id,))
        row = c.fetchone()
        return json.loads(row[0]) if row else None

    def read_observation(self, record_id: str) -> dict[str, Any] | None:
        c = self._conn.cursor()
        c.execute("SELECT json_payload FROM observations WHERE record_id = ?", (record_id,))
        row = c.fetchone()
        return json.loads(row[0]) if row else None

    def read_entity(self, record_id: str) -> dict[str, Any] | None:
        c = self._conn.cursor()
        c.execute("SELECT json_payload FROM entities WHERE record_id = ?", (record_id,))
        row = c.fetchone()
        return json.loads(row[0]) if row else None

    def read_edge(self, record_id: str) -> dict[str, Any] | None:
        c = self._conn.cursor()
        c.execute("SELECT json_payload FROM edges WHERE record_id = ?", (record_id,))
        row = c.fetchone()
        return json.loads(row[0]) if row else None

    def read_procedure(self, record_id: str) -> dict[str, Any] | None:
        c = self._conn.cursor()
        c.execute("SELECT json_payload FROM procedures WHERE record_id = ?", (record_id,))
        row = c.fetchone()
        return json.loads(row[0]) if row else None

    def read_decision_trace(self, record_id: str) -> dict[str, Any] | None:
        c = self._conn.cursor()
        c.execute("SELECT json_payload FROM decision_traces WHERE record_id = ?", (record_id,))
        row = c.fetchone()
        return json.loads(row[0]) if row else None

    def read_agent_task(self, task_id: str) -> dict[str, Any] | None:
        c = self._conn.cursor()
        c.execute("SELECT * FROM agent_tasks WHERE task_id = ?", (task_id,))
        row = c.fetchone()
        if not row:
            return None
        return {
            "task_id": row[0], "dependencies": json.loads(row[1] or "[]"),
            "status": row[2], "assigned_agent": row[3],
            "evidence_id": row[4], "locks": json.loads(row[5] or "[]"),
            "created_at": row[6],
        }

    def list_artifacts(self, limit: int = 100) -> list[dict[str, Any]]:
        c = self._conn.cursor()
        c.execute("SELECT json_payload FROM artifacts ORDER BY created_at DESC LIMIT ?", (limit,))
        return [json.loads(r[0]) for r in c.fetchall()]

    def list_observations(self, limit: int = 100) -> list[dict[str, Any]]:
        c = self._conn.cursor()
        c.execute("SELECT json_payload FROM observations ORDER BY created_at DESC LIMIT ?", (limit,))
        return [json.loads(r[0]) for r in c.fetchall()]

    def list_entities(self, limit: int = 100) -> list[dict[str, Any]]:
        c = self._conn.cursor()
        c.execute("SELECT json_payload FROM entities ORDER BY created_at DESC LIMIT ?", (limit,))
        return [json.loads(r[0]) for r in c.fetchall()]

    def list_edges(self, limit: int = 100) -> list[dict[str, Any]]:
        c = self._conn.cursor()
        c.execute("SELECT json_payload FROM edges ORDER BY created_at DESC LIMIT ?", (limit,))
        return [json.loads(r[0]) for r in c.fetchall()]

    def list_procedures(self, limit: int = 100) -> list[dict[str, Any]]:
        c = self._conn.cursor()
        c.execute("SELECT json_payload FROM procedures ORDER BY created_at DESC LIMIT ?", (limit,))
        return [json.loads(r[0]) for r in c.fetchall()]

    def list_decision_traces(self, limit: int = 100) -> list[dict[str, Any]]:
        c = self._conn.cursor()
        c.execute("SELECT json_payload FROM decision_traces ORDER BY created_at DESC LIMIT ?", (limit,))
        return [json.loads(r[0]) for r in c.fetchall()]

    def list_agent_tasks(self, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        c = self._conn.cursor()
        if status:
            c.execute("SELECT * FROM agent_tasks WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                      (status, limit))
        else:
            c.execute("SELECT * FROM agent_tasks ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        return [
            {
                "task_id": r[0], "dependencies": json.loads(r[1] or "[]"),
                "status": r[2], "assigned_agent": r[3],
                "evidence_id": r[4], "locks": json.loads(r[5] or "[]"),
                "created_at": r[6],
            }
            for r in rows
        ]

    def count(self, table: str) -> int:
        c = self._conn.cursor()
        c.execute(f"SELECT COUNT(*) FROM {table}")
        return c.fetchone()[0]

    def stats(self) -> dict[str, int]:
        tables = [
            "artifacts", "observations", "entities", "edges",
            "version_relations", "summaries", "procedures",
            "decision_traces", "agent_tasks", "access_index",
            "mental_models", "skill_library_entries",
        ]
        return {t: self.count(t) for t in tables}

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "CanonicalStore":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
