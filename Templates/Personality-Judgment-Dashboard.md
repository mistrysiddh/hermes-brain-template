# Personality Judgment Dashboard

A dynamic Dataview-powered dashboard for tracking and visualizing personality judgment analyses.

## 📊 Active Analyses

```dataview
TABLE
  file.link AS "Analysis",
  subject AS "Subject",
  period AS "Period",
  primary_style AS "Primary Style",
  top_hypothesis AS "Top Hypothesis",
  confidence AS "Confidence",
  file.mtime AS "Updated"
FROM "Templates/Personality-Judgment-Analysis.md" AND "-Template"
WHERE contains(file.name, "Analysis") OR contains(file.name, "Judgment")
SORT file.mtime DESC
```

## 📈 Confidence Distribution

```dataviewjs
const dv = app.plugins.plugins.dataview.api;
const pages = dv.pages('"Templates/Personality-Judgment-Analysis.md"')
  .where(p => p.file.name !== "Personality-Judgment-Analysis.md");

const confidenceCounts = {
  High: 0,
  Medium: 0,
  Low: 0,
  "Very Low": 0
};

for (const p of pages) {
  const conf = p.confidence ? p.confidence.toString().trim() : "Unknown";
  if (confidenceCounts[conf] !== undefined) {
    confidenceCounts[conf]++;
  }
}

dv.table(["Confidence Level", "Count"], 
  Object.entries(confidenceCounts).filter(([_, count]) => count > 0)
    .map(([level, count]) => [level, count])
);
```

## 🔍 Recent Hypotheses

```dataview
TABLE
  hypothesis AS "Hypothesis",
  context AS "Context",
  evidence_supporting AS "Supporting Evidence",
  confidence AS "Confidence"
FROM "Templates/Personality-Judgment-Analysis.md" AND "-Template"
FLATTEN file.hypotheses AS hypothesis
WHERE hypothesis
SORT file.mtime DESC
LIMIT 10
```

## 📅 Analysis Timeline

```dataview
TIMELINE
  file.mtime AS "Date"
  FROM "Templates/Personality-Judgment-Analysis.md" AND "-Template"
  WHERE file.name !== "Personality-Judgment-Analysis.md"
  GROUP BY dateformat(file.mtime, "yyyy-MM") AS "Month"
```

## 🏷️ Topics Analyzed

```dataviewjs
const dv = app.plugins.plugins.dataview.api;
const pages = dv.pages('"Templates/Personality-Judgment-Analysis.md"')
  .where(p => p.file.name !== "Personality-Judgment-Analysis.md");

const topicCounts = {};

for (const p of pages) {
  if (p.topic_behavior) {
    // Assuming topic_behavior is a list of topics analyzed
    const topics = Array.isArray(p.topic_behavior) ? p.topic_behavior : [p.topic_behavior];
    for (const topic of topics) {
      topicCounts[topic] = (topicCounts[topic] || 0) + 1;
    }
  }
}

const sortedTopics = Object.entries(topicCounts)
  .sort((a, b) => b[1] - a[1])
  .slice(0, 10);

dv.table(["Topic", "Analyses Count"], sortedTopics);
```

## ⚠️ Active Anomalies

```dataview
TABLE
  anomaly_dimension AS "Dimension",
  anomaly_observed AS "Observation",
  context AS "Context"
FROM "Templates/Personality-Judgment-Analysis.md" AND "-Template"
FLATTEN file.anomalies AS anomaly
WHERE anomaly
SORT file.mtime DESC
```

## 💡 Recommendations Summary

```dataview
LIST
  file.recommendations AS "Recommendation"
FROM "Templates/Personality-Judgment-Analysis.md" AND "-Template"
FLATTEN file.recommendations AS recommendation
WHERE recommendation
LIMIT 20
```

---
*Dashboard updates automatically as you create and update personality judgment analyses*
*Last updated: {{date}}*