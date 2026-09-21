# Personality Judgment Dashboard

A dynamic Dataview-powered dashboard for tracking and visualizing personality judgment analyses.

## 📊 Active Analyses

```dataview
TABLE
  subject AS "Subject",
  period AS "Period",
  primary_style AS "Primary Style",
  top_hypothesis AS "Top Hypothesis",
  confidence AS "Confidence",
  dateformat(file.mtime, "yyyy-MM-dd") AS "Updated"
FROM #personality-judgment or "04-Archives/Daily" or "Daily"
WHERE subject AND file.name != "Personality-Judgment-Analysis.md" AND file.name != "Personality-Judgment-Dashboard.md"
SORT file.mtime DESC
```

## 📈 Confidence Distribution

```dataviewjs
const pages = dv.pages('#personality-judgment or "04-Archives/Daily" or "Daily"')
  .where(p => p.file.name !== "Personality-Judgment-Analysis.md" && p.file.name !== "Personality-Judgment-Dashboard.md" && p.subject);

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
  subject AS "Subject",
  confidence AS "Confidence"
FROM #personality-judgment or "04-Archives/Daily" or "Daily"
WHERE file.name != "Personality-Judgment-Analysis.md" AND file.name != "Personality-Judgment-Dashboard.md" AND hypotheses
FLATTEN hypotheses AS hypothesis
WHERE hypothesis
SORT file.mtime DESC
LIMIT 10
```

## 📅 Analysis Timeline

```dataview
TABLE WITHOUT ID
  dateformat(file.mtime, "yyyy-MM-dd") AS "Date",
  file.link AS "Analysis",
  subject AS "Subject",
  primary_style AS "Style",
  confidence AS "Confidence"
FROM #personality-judgment or "04-Archives/Daily" or "Daily"
WHERE file.name != "Personality-Judgment-Analysis.md" AND file.name != "Personality-Judgment-Dashboard.md" AND subject
SORT file.mtime DESC
```

## 🏷️ Topics Analyzed

```dataviewjs
const pages = dv.pages('#personality-judgment or "04-Archives/Daily" or "Daily"')
  .where(p => p.file.name !== "Personality-Judgment-Analysis.md" && p.file.name !== "Personality-Judgment-Dashboard.md" && p.topic_behavior);

const topicCounts = {};

for (const p of pages) {
  if (p.topic_behavior) {
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
  anomaly AS "Anomaly",
  subject AS "Subject",
  file.link AS "Analysis"
FROM #personality-judgment or "04-Archives/Daily" or "Daily"
WHERE file.name != "Personality-Judgment-Analysis.md" AND file.name != "Personality-Judgment-Dashboard.md" AND anomalies
FLATTEN anomalies AS anomaly
WHERE anomaly
SORT file.mtime DESC
```

## 💡 Recommendations Summary

```dataview
LIST
  recommendation
FROM #personality-judgment or "04-Archives/Daily" or "Daily"
WHERE file.name != "Personality-Judgment-Analysis.md" AND file.name != "Personality-Judgment-Dashboard.md" AND recommendations
FLATTEN recommendations AS recommendation
WHERE recommendation
LIMIT 20
```

---
*Dashboard updates automatically as you create and update personality judgment analyses*
*Last updated: {{date}}*