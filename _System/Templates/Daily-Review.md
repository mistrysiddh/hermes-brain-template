---
type: daily-review
status: draft
created: {{date}}
tags: [daily-review]
---

# Daily Review — {{date}}

## 💬 Sessions for this day

```dataview
TABLE file.mtime AS "Modified", file.size AS "Size"
FROM "04-Archives/Daily" OR "Daily"
WHERE (file.folder = this.file.folder + "/" + this.file.name OR file.folder = this.file.folder) AND file.name != this.file.name AND file.name != "README" AND file.name != "manifest" AND !contains(file.tags, "daily-review")
SORT file.name ASC
```

## Sessions reviewed
- 


## Durable facts found
- [ ] 

## Flagged for Memory-Review
- 

## Notes / follow-ups
- 

---
See [[04-Archives/Memory-Review/TEMPLATE|Memory-Review promotion criteria]] before staging anything as a candidate.
