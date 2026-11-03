---
name: knowledge-management
description: Knowledge Management skill — openKMS-style decision systems, explicit rules, multi-relational ontology, dataset registration, and knowledge map generation for the Hermes Brain vault.
tools:
  - repository
---

# knowledge_management.py — Knowledge Management Skill

Open Knowledge Management System concepts brought to the Hermes Brain vault:

- **Decision systems**: case → conclusion with explicit basis, computation, and boundary
- **Rules**: explicit, versioned, changeable by business experts
- **Knowledge base**: articles, glossary, wiki, KB entries
- **Ontology**: objects, links, functions, actions
- **Datasets**: registers, columns, keys, AI context, relationships, quality
- **Knowledge map**: visualize and navigate knowledge structure

## What it does

| Subcommand | What it does |
|------------|--------------|
| `kb-add-article` | Add a knowledge article with title, content, author, tags |
| `kb-list-articles` | List all knowledge articles |
| `kb-get-article` | Get a specific article by ID |
| `ds-add-decision` | Add a decision: case → conclusion with basis, computation, boundary |
| `ds-list-decisions` | List all decision system records |
| `rule-add` | Add an explicit, versioned rule with condition, action, priority |
| `rule-list` | List all rules |
| `ontology-add-object` | Add an ontology object with type and properties |
| `ontology-add-link` | Add an ontology link between two objects |
| `ontology-list-objects` | List all ontology objects |
| `ontology-list-links` | List all ontology links |
| `dataset-register` | Register a dataset with columns, keys, AI context, relationships |
| `dataset-list` | List all registered datasets |
| `knowledge-map` | Generate knowledge map: overview of all knowledge artifacts |

## Data model

Each knowledge artifact is stored as JSONL in `_System/KnowledgeBase/`:
- `articles.jsonl` — knowledge articles
- `decisions.jsonl` — decision system records (case → conclusion)
- `rules.jsonl` — explicit, versioned rules
- `ontology_objects.jsonl` — ontology objects
- `ontology_links.jsonl` — ontology links between objects
- `datasets.jsonl` — registered datasets

## Usage

```
@hermes-brain knowledge-management --vault <path> ds-add-decision --case "..." --conclusion "..." --basis "..." --computation "..." --boundary "..."
@hermes-brain knowledge-management --vault <path> kb-add-article --title "..." --content "..." --author "..." --tags "tag1,tag2"
@hermes-brain knowledge-management --vault <path> rule-add --name "..." --condition "..." --action "..." --priority 1
@hermes-brain knowledge-management --vault <path> ontology-add-object --id "obj_1" --type "Person" --properties '{"name": "Alice"}'
@hermes-brain knowledge-management --vault <path> dataset-register --name "customer_data" --columns '["id","name","email"]' --keys '["id"]'
@hermes-brain knowledge-management --vault <path> knowledge-map
```

All commands support `--dry-run` (default) or `--apply` to write changes.

---

Built for the Hermes Brain template — multi-agent persistent memory vault for AI agents.
