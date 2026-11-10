---
name: smart-memory
description: Smart Memory & RAG skill — agentic memory with System-One control plane, multi-relational storage (semantic, temporal, causal, entity), RAG retrieval, and model routing by complexity. Open model support, not tied to paid Jev API.
tools:
  - repository
---

# smart_memory.py — Smart Memory & RAG Skill

Agentic memory system inspired by Jev-Mem and laya-jev-GraphRAG:

- **System-One control plane**: Fast heuristic decisions for memory routing and budget
- **Multi-relational memory plane**: semantic, temporal, causal, entity relations
- **System-Two reasoning**: Invoked only for genuine synthesis
- **Open model support**: Works with any local/open model, not tied to paid Jev API
- **Data type awareness**: Different handling for different memory data types

## What it does

| Subcommand | What it does |
|------------|--------------|
| `add` | Add a memory to a relation type (semantic, temporal, causal, entity) |
| `retrieve` | Retrieve relevant memories using System-One heuristic scoring |
| `rag` | RAG retrieval — format retrieved memories as context for synthesis |
| `route` | System-One route decision — pick relation types by task complexity |
| `budget` | Memory budget check — estimate memory size vs budget |

## Relation Types

| Type | Purpose |
|------|---------|
| semantic | Conceptual meaning and topic similarity |
| temporal | Time-based relationships and sequences |
| causal | Cause-effect relationships between events |
| entity | Entity-mention and person/place/organization links |

## Memory Model

Each memory stores: content, relation type, source, confidence, tags, access count, last accessed, and a lightweight embedding for fast similarity search.

## Usage

```
@hermes-brain smart-memory --vault <path> add --content "..." --rel-type semantic --confidence 0.9
@hermes-brain smart-memory --vault <path> retrieve --query "..." --rel-types semantic,entity --top-k 5
@hermes-brain smart-memory --vault <path> rag --query "..." --top-k 5
@hermes-brain smart-memory --vault <path> route --complexity 0.8
@hermes-brain smart-memory --vault <path> budget --tokens 5000 --budget-mb 50
```

All commands support `--dry-run` (default) or `--apply` to write changes.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
