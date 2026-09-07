# Chat ↔ Skill ↔ Profile Correlation (Live)

Correlates archived chats by **source type** and **file pattern** in real
time via Dataview — useful once `Daily/` has real session exports flowing
into it.

## By source pattern

```dataviewjs
const pages = dv.pages('"Daily"').where(p => !["README","manifest","Timeline","Chat-Correlation"].includes(p.file.name));
const buckets = {"🧠 memory digest": [], "☁️ supermemory import": [], "⏰ cron run": [], "💬 local session": []};
for (const p of pages) {
  const n = p.file.name;
  if (n.includes("supermemory_memory-entries")) buckets["🧠 memory digest"].push(p);
  else if (n.startsWith("supermemory_")) buckets["☁️ supermemory import"].push(p);
  else if (n.startsWith("cron_")) buckets["⏰ cron run"].push(p);
  else buckets["💬 local session"].push(p);
}
dv.table(["Pattern", "Count"], Object.entries(buckets).map(([k,v]) => [k, v.length]));
```

## By profile (if you run multiple agent profiles)

If you're running more than one Hermes profile against this vault, filter
sessions by whatever naming convention you use for each profile — swap the
`contains(...)` terms below for your own profile names.

```dataview
LIST
FROM "Daily"
WHERE contains(file.name, "example-profile-name")
SORT file.name ASC
```

## By skill (optional, static)

If you maintain a `Skills-Notes/Skill-to-Chat-Links.md` mapping which
archived sessions used which Hermes skill, link it here. This template
doesn't ship one — build it yourself once you have real session history, or
see [[Dataview-Query-Library]] for a starting-point query.

---

Cross-links: [[Timeline]] (full chronological browse) · [[README]] (folder conventions) · [[../Skills-Notes/Dataview-Query-Library]] · [[../Projects/README]] (pipeline overview)
