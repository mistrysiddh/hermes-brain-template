# Daily Timeline

A single chronological view connecting every archived chat across
`Daily/YYYY/MM/DD/`. Requires the **Dataview** plugin (already enabled in
this vault) to render live; without it this shows as raw code blocks
instead of tables.

Use this instead of clicking through date folders one at a time: sort by
date, filter by source, or search within the rendered table (Ctrl/Cmd+F).

## Full chronological index

```dataview
TABLE
    choice(contains(file.name, "supermemory_memory-entries"), "🧠 memory digest",
    choice(contains(file.name, "supermemory_"), "☁️ supermemory import",
    choice(contains(file.name, "cron_"), "⏰ cron run", "💬 session"))) AS Type,
    file.folder AS "Date folder"
FROM "Daily"
WHERE file.name != "README" AND file.name != "manifest" AND file.name != "Timeline"
SORT file.folder ASC, file.name ASC
```

## Recent 20 (most recently modified)

```dataview
TABLE file.mtime AS "Modified", file.folder AS "Date folder"
FROM "Daily"
WHERE file.name != "README" AND file.name != "manifest" AND file.name != "Timeline"
SORT file.mtime DESC
LIMIT 20
```

## By month

```dataviewjs
const pages = dv.pages('"Daily"').where(p => !["README","manifest","Timeline"].includes(p.file.name));
const byMonth = {};
for (const p of pages) {
  const parts = p.file.folder.split("/");
  // Daily/YYYY/MM/DD -> parts = [Daily, YYYY, MM, DD]
  if (parts.length >= 3) {
    const key = `${parts[1]}-${parts[2]}`;
    byMonth[key] = (byMonth[key] || 0) + 1;
  }
}
const rows = Object.entries(byMonth).sort((a,b) => a[0] < b[0] ? 1 : -1);
dv.table(["Month", "Files"], rows);
```

---

See also: [[README]] (Daily folder conventions), [[../Projects/README]] (pipeline overview).

This page (and [[Chat-Correlation]]) were adapted from a real working vault
that also imports Supermemory session data — the `supermemory_` filename
pattern is matched defensively above in case you wire that up too, but it's
entirely optional and unused by the base template.
