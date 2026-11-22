---
title: Wiki Schema — LLM Maintenance Guide
type: schema
status: active
---

# Wiki Schema — LLM Maintenance Guide

This is the schema file that tells the LLM agent how to structure, maintain, and update the wiki at `02-Areas/Wiki/`. You (the human) and the LLM co-evolve this over time.

## Directory layout

```
02-Areas/Wiki/
├── README.md            # Wiki entry point (this directory's front door)
├── index.md             # Content catalog — every page listed with link + summary
├── entities/            # People, companies, products, tools
│   └── README.md        # Entity index
├── concepts/            # Ideas, techniques, patterns
│   └── README.md        # Concept index
├── comparisons/         # Head-to-head comparisons
│   └── README.md        # Comparison index
├── sources/             # Summaries of ingested sources
│   └── README.md        # Source index
└── synthesis/           # Cross-cutting analyses
    └── README.md        # Synthesis index
```

## File format (every wiki page)

```markdown
---
title: <Page Title>
type: entity|concept|comparison|source|synthesis
status: stub|growing|mature|archived
aliases: <comma-separated aliases>
sources: <comma-separated links to 03-Resources/Sources/>
updated: YYYY-MM-DD
---

# <Page Title>

## Summary

One paragraph: what is this, why does it matter.

## Key Points

- Bullet points of the most important facts/ideas.

## Connections

Links to related wiki pages:
- [[../../02-Areas/Wiki/entities/related-entity.md|Related Entity]]
- [[../../02-Areas/Wiki/concepts/related-concept.md|Related Concept]]

## Sources

- [[../../03-Resources/Sources/source-name.md|Source Name]] — what was extracted from it.

## Notes

Free-form notes, contradictions flagged, open questions, next steps.
```

## Workflows

### 1. Ingest a new source

When a new file appears in `03-Resources/Sources/`:

1. Read the source file.
2. Discuss key takeaways with the human (ask clarifying questions if needed).
3. Write a summary page at `02-Areas/Wiki/sources/<source-name>.md`.
4. Update `02-Areas/Wiki/sources/README.md` index.
5. For each important entity/concept mentioned:
   - Create or update its page in `entities/` or `concepts/`.
   - Add a link back to the source summary.
6. Update `02-Areas/Wiki/index.md` with the new page.
7. Append an entry to `04-Archives/Audit-Reports/WIKI-LOG.md`:
   ```
   ## [YYYY-MM-DD] ingest | Source Name
   - Wrote summary at ...
   - Updated entity page ...
   - Updated concept page ...
   ```
8. Notify the human: "Source ingested. Wiki pages updated: X, Y, Z."

### 2. Answer a question against the wiki

1. Read `02-Areas/Wiki/index.md` to find relevant pages.
2. Drill into those pages.
3. Synthesize an answer with citations (links to wiki pages and sources).
4. If the answer is a valuable new insight (comparison, analysis, connection discovered), write it as a new page in `synthesis/` and add it to `index.md`.
5. Append a query entry to `WIKI-LOG.md`.

### 3. Lint the wiki (periodically)

Run a health check and look for:

- **Contradictions** — two pages saying different things about the same topic
- **Stale claims** — pages that newer sources have superseded
- **Orphan pages** — pages with no inbound links
- **Missing pages** — important concepts mentioned but lacking their own page
- **Missing cross-references** — pages that should link to each other but don't

For each finding, either fix it directly or ask the human for guidance. Append lint results to `WIKI-LOG.md`.

## Index maintenance

`02-Areas/Wiki/index.md` should be organized by category:

```markdown
## Entities

- [[entities/person-a.md|Person A]] — summary
- [[entities/tool-b.md|Tool B]] — summary

## Concepts

- [[concepts/concept-x.md|Concept X]] — summary

## Comparisons

- [[comparisons/x-vs-y.md|X vs Y]] — summary

## Sources

- [[sources/source-1.md|Source 1]] — summary

## Synthesis

- [[synthesis/topic.md|Topic Analysis]] — summary
```

The LLM updates this on every ingest.

## Log format

`04-Archives/Audit-Reports/WIKI-LOG.md` is append-only. Each entry:

```markdown
## [YYYY-MM-DD] ingest | Source Name
- Action taken
- Pages created/updated

## [YYYY-MM-DD] query | Question summary
- Answer provided
- New page written at ...

## [YYYY-MM-DD] lint | Health check
- Issues found: N
- Issues fixed: N
```

## Human-in-the-loop

The LLM owns the wiki layer entirely, but you (the human) are in charge of:
- Sourcing (what goes into `03-Resources/Sources/`)
- Directing analysis (what to focus on)
- Asking good questions
- Reviewing and approving major structural changes

The LLM never deletes a page without asking you first. When in doubt, ask.
