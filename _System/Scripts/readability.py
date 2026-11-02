#!/usr/bin/env python3
"""
Hermes Brain — Readability Metrics Skill (readability.py)

Computes human-readability grades for vault notes:
- Coleman-Liau Index (most writing)
- Dale-Chall Readability Formula (with common-word list)
- FORCAST (bullet-points, fragments, short text)
- PMOSE/IKIRSCH (tables, forms, structured content)
- Chinese readability reference (ALTA2022Readability)

Multi-harness compatible:
  - --vault CLI arg (never module-level path resolution)
  - Path resolution deferred to main() after argument parsing
  - --dry-run default / --apply for human-in-the-loop approval
  - Stdlib-only
  - --test self-tests (4/4)

Subcommands:
  readability.py scan       Scan vault notes for readability (dry-run report)
  readability.py --test     Built-in self-test suite

Usage:
  python readability.py --vault <path> scan --days 30
  python readability.py --vault <path> scan --days 30 --apply
  python readability.py --vault <path> --test

Exit code: 0 always (reporting tool, not a gate)
"""

import argparse
import datetime
import os
import re
import sys

# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at import time
# ---------------------------------------------------------------------------
VAULT = None
READABILITY_DIR = None


def init_paths(vault_path):
    """Resolve all vault-relative paths from the given vault root."""
    global VAULT, READABILITY_DIR
    VAULT = os.path.abspath(vault_path)
    READABILITY_DIR = os.path.join(VAULT, "04-Archives", "Readability")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def read_file(path):
    if not os.path.exists(path):
        return ""
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def walk_md(vault_dir, exclude_dirs=None, exclude_files=None):
    """Walk vault_dir yielding (full_path, rel_path, name, content) for .md files."""
    exclude_dirs = exclude_dirs or {".obsidian", ".git", ".trash", ".sota"}
    exclude_files = exclude_files or {"README.md", "manifest.jsonl"}
    for root, dirs, files in os.walk(vault_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]
        for f in sorted(files):
            if not f.endswith(".md"):
                continue
            if f in exclude_files:
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, vault_dir).replace("\\", "/")
            content = read_file(full)
            yield full, rel, os.path.splitext(f)[0], content


# ---------------------------------------------------------------------------
# Text statistics
# ---------------------------------------------------------------------------
def count_syllables(word):
    """Estimate syllable count for an English word."""
    word = word.lower().strip(".,!?;:\"'()[]{}")
    if not word:
        return 0
    if len(word) <= 3:
        return 1
    # Remove silent e
    word = re.sub(r"e$", "", word)
    # Count vowel groups
    groups = re.findall(r"[aeiouy]+", word)
    return max(1, len(groups))


def is_monosyllabic(word):
    return count_syllables(word) == 1


def count_sentences(text):
    """Count sentences by splitting on sentence-ending punctuation."""
    # Split on . ! ? followed by space or end
    parts = re.split(r"[.!?]+[\s]+|[.!?]+$", text.strip())
    parts = [p for p in parts if p.strip()]
    return len(parts) if parts else 1


def count_words(text):
    """Count words (alphanumeric sequences)."""
    return len(re.findall(r"\b[a-zA-Z][a-zA-Z'-]+\b", text))


def count_letters(text):
    """Count alphabetic characters."""
    return len(re.findall(r"[a-zA-Z]", text))


def get_text_stats(text):
    """Return words, sentences, letters, syllables, monosyllabic count."""
    words = re.findall(r"\b[a-zA-Z][a-zA-Z'-]+\b", text)
    word_count = len(words)
    sentence_count = count_sentences(text)
    letter_count = count_letters(text)
    syllable_count = sum(count_syllables(w) for w in words)
    mono_count = sum(1 for w in words if is_monosyllabic(w))
    return {
        "words": word_count,
        "sentences": sentence_count,
        "letters": letter_count,
        "syllables": syllable_count,
        "monosyllabic": mono_count,
    }


# ---------------------------------------------------------------------------
# Readability formulas
# ---------------------------------------------------------------------------
def coleman_liau_index(text):
    """
    Coleman-Liau Index: CLI = 0.0588 * L - 0.296 * S - 15.8
    L = letters per 100 words, S = sentences per 100 words.
    Returns grade level (approx US school grade).
    """
    stats = get_text_stats(text)
    words = stats["words"]
    if words == 0:
        return {"score": 0.0, "grade": "N/A", "label": "No text"}
    L = stats["letters"] / words * 100
    S = stats["sentences"] / words * 100
    score = 0.0588 * L - 0.296 * S - 15.8
    return {
        "score": round(score, 1),
        "grade": round(score),
        "label": _grade_label(round(score)),
    }


def _grade_label(grade):
    if grade <= 1:
        return "Very easy (1st grade)"
    elif grade <= 3:
        return "Easy (2nd–3rd grade)"
    elif grade <= 5:
        return "Fairly easy (4th–5th grade)"
    elif grade <= 7:
        return "Standard (6th–7th grade)"
    elif grade <= 9:
        return "Fairly difficult (8th–9th grade)"
    elif grade <= 11:
        return "Difficult (10th–11th grade)"
    elif grade <= 13:
        return "Very difficult (college)"
    else:
        return "Extremely difficult (college graduate+)"


DALE_CHALL_COMMON_WORDS = {
    "a", "about", "above", "across", "after", "again", "against", "all", "almost",
    "alone", "along", "already", "also", "although", "always", "am", "among",
    "an", "and", "any", "anyone", "anything", "appear", "apple", "are", "around",
    "as", "ask", "at", "ate", "away", "baby", "back", "bad", "bag", "ball",
    "bank", "bar", "base", "bat", "be", "bear", "beat", "beautiful", "because",
    "become", "been", "before", "began", "begin", "behind", "being", "believe",
    "best", "better", "between", "big", "bird", "bit", "black", "block", "blood",
    "blow", "blue", "board", "boat", "body", "bone", "book", "border", "borrow",
    "both", "box", "boy", "branch", "break", "breakfast", "brick", "bridge",
    "bright", "bring", "broad", "broke", "brown", "build", "burn", "bus",
    "business", "but", "buy", "by", "cake", "call", "came", "camp", "can",
    "cannot", "car", "card", "care", "carry", "case", "cat", "catch",
    "cause", "cell", "cent", "center", "central", "century", "certain",
    "chair", "chance", "change", "cheap", "check", "cheese", "chest",
    "chicken", "chief", "child", "children", "choice", "choose", "church",
    "city", "class", "clean", "clear", "climb", "clock", "close", "cloth",
    "cloud", "club", "coal", "coat", "cold", "collect", "college", "color",
    "come", "comfortable", "command", "common", "community", "company",
    "compare", "complete", "complex", "condition", "consider", "contain",
    "continue", "cost", "could", "count", "country", "county", "couple",
    "course", "court", "cover", "cow", "create", "cross", "crowd", "cry",
    "cut", "daily", "damage", "dance", "danger", "dark", "day", "dead",
    "deal", "death", "decide", "deep", "department", "depend", "describe",
    "desert", "design", "desk", "detail", "develop", "die", "difference",
    "difficult", "dinner", "direct", "dirt", "dirty", "discover", "discuss",
    "disease", "dish", "distance", "divide", "doctor", "dog", "door", "down",
    "draw", "dream", "dress", "drink", "drive", "drop", "dry", "duck",
    "during", "dust", "duty", "each", "ear", "early", "earn", "earth",
    "east", "easy", "eat", "edge", "educate", "effect", "effort", "egg",
    "eight", "either", "electric", "element", "else", "end", "enemy",
    "engine", "english", "enjoy", "enough", "enter", "equal", "error",
    "escape", "especially", "essential", "establish", "even", "evening",
    "event", "ever", "every", "everyone", "except", "expect", "experience",
    "experiment", "explain", "express", "eye", "face", "fact", "fail",
    "fair", "fall", "family", "famous", "farm", "farmer", "fast", "father",
    "favor", "fear", "feed", "feel", "few", "field", "fight", "fill",
    "film", "final", "find", "fine", "finger", "finish", "fire", "firm",
    "first", "fish", "five", "floor", "flower", "fly", "fold", "follow",
    "food", "foot", "force", "foreign", "forest", "forget", "fork", "form",
    "forty", "forward", "four", "free", "french", "fresh", "friend", "from",
    "front", "fruit", "fuel", "full", "fun", "game", "garage", "garden",
    "gas", "gate", "general", "gentle", "get", "girl", "give", "glad",
    "glass", "go", "god", "gold", "good", "government", "grade", "grain",
    "grand", "grass", "gray", "great", "green", "ground", "group", "grow",
    "guard", "guess", "guide", "gun", "hair", "half", "hall", "hand",
    "handle", "hang", "happen", "happy", "hard", "has", "hat", "have",
    "he", "head", "hear", "heart", "heat", "heavy", "help", "her",
    "here", "high", "him", "his", "history", "hit", "hold", "hole",
    "holiday", "home", "honest", "hope", "horse", "hospital", "hot",
    "hotel", "hour", "house", "how", "however", "huge", "human", "hundred",
    "husband", "ice", "idea", "identify", "if", "image", "imagine",
    "important", "improve", "in", "include", "income", "increase",
    "indeed", "index", "indicate", "individual", "industry", "information",
    "instead", "instrument", "insurance", "interest", "international",
    "interview", "into", "introduce", "invent", "investment", "invite",
    "involve", "iron", "is", "issue", "it", "item", "its", "itself",
    "job", "join", "judge", "jump", "just", "keep", "key", "kill",
    "kind", "king", "kitchen", "know", "knowledge", "labor", "lack",
    "lady", "lake", "lamp", "land", "language", "large", "last", "late",
    "later", "laugh", "law", "lawyer", "lay", "lead", "leader", "learn",
    "least", "leave", "left", "leg", "legal", "less", "lesson", "let",
    "letter", "level", "library", "lie", "life", "light", "like", "limit",
    "line", "link", "lion", "list", "listen", "little", "live", "living",
    "load", "loan", "local", "location", "long", "look", "lose", "loss",
    "lost", "lot", "love", "low", "luck", "lunch", "machine", "magazine",
    "mail", "main", "maintain", "major", "make", "man", "manage", "manager",
    "many", "mark", "market", "marriage", "married", "marry", "mask",
    "mass", "master", "match", "material", "mathematics", "matter", "may",
    "maybe", "me", "meal", "mean", "meaning", "measure", "meat", "medical",
    "meet", "meeting", "member", "memory", "mention", "menu", "merely",
    "method", "middle", "might", "mile", "military", "milk", "mill",
    "mind", "mine", "minute", "mirror", "miss", "mistake", "mix", "model",
    "modern", "moment", "money", "month", "mood", "moon", "more", "morning",
    "most", "mother", "motion", "motor", "mountain", "mouse", "mouth",
    "move", "movie", "much", "mud", "music", "must", "my", "myself",
    "name", "nation", "national", "natural", "nature", "near", "nearly",
    "necessary", "neck", "need", "needle", "negative", "neighbor", "neither",
    "nerve", "net", "never", "new", "news", "next", "nice", "night",
    "nine", "no", "nobody", "nod", "noise", "none", "noon", "nor", "north",
    "nose", "not", "note", "nothing", "notice", "novel", "now", "number",
    "numerous", "nurse", "object", "observe", "occasion", "occur", "ocean",
    "of", "off", "offer", "office", "officer", "official", "often", "oh",
    "oil", "okay", "old", "on", "once", "one", "only", "onto", "open",
    "operate", "opinion", "opportunity", "oppose", "or", "orange", "order",
    "ordinary", "organize", "other", "ought", "our", "out", "outcome",
    "outside", "over", "own", "owner", "page", "pain", "paint", "pair",
    "palace", "pan", "paper", "parent", "park", "part", "partner", "party",
    "pass", "past", "path", "pattern", "pay", "payment", "peace", "pen",
    "pencil", "people", "per", "percent", "perfect", "perform", "perhaps",
    "period", "person", "personal", "pet", "phase", "phone", "photo",
    "phrase", "physical", "piano", "pick", "picture", "piece", "pig",
    "pile", "pilot", "pin", "pink", "pipe", "place", "plan", "plane",
    "plant", "plastic", "plate", "platform", "play", "player", "please",
    "pleasure", "plenty", "plus", "pocket", "poem", "poet", "poetry",
    "point", "pole", "police", "policy", "political", "politics", "pool",
    "poor", "pop", "popular", "position", "positive", "possible", "post",
    "pot", "potato", "pound", "power", "practice", "prefer", "prepare",
    "present", "president", "press", "pressure", "pretty", "prevent",
    "previous", "price", "pride", "primary", "prime", "prince", "princess",
    "print", "prior", "priority", "prison", "private", "prize", "problem",
    "proceed", "process", "produce", "product", "production", "profession",
    "professional", "professor", "profile", "profit", "program", "progress",
    "project", "promise", "promote", "proof", "proper", "property",
    "proposal", "propose", "propose", "protect", "prove", "provide",
    "public", "pull", "pump", "punish", "pupil", "purchase", "pure",
    "purpose", "push", "put", "quality", "quarter", "queen", "question",
    "quick", "quiet", "quit", "quite", "quote", "race", "radio", "rail",
    "rain", "raise", "range", "rapid", "rare", "rate", "rather", "raw",
    "reach", "read", "ready", "real", "reality", "realize", "really",
    "reason", "receive", "recent", "record", "red", "reduce", "refer",
    "reflect", "reform", "refuse", "regard", "region", "regular", "reject",
    "relate", "relation", "relationship", "relative", "relax", "release",
    "relevant", "rely", "remain", "remember", "remind", "remote", "remove",
    "rent", "repair", "repeat", "replace", "reply", "report", "represent",
    "request", "require", "research", "reserve", "resident", "resist",
    "resolve", "resource", "respect", "respond", "response", "responsible",
    "rest", "restaurant", "result", "return", "reveal", "review", "revolution",
    "reward", "rhythm", "rice", "rich", "ride", "right", "ring", "rise",
    "risk", "river", "road", "rock", "role", "roll", "roof", "room", "root",
    "rope", "rose", "rough", "round", "route", "row", "royal", "rule",
    "run", "rush", "sad", "safe", "safety", "sail", "salad", "salary",
    "sale", "salt", "same", "sample", "sand", "satisfy", "sauce", "save",
    "say", "scale", "scene", "schedule", "scheme", "school", "science",
    "score", "scratch", "screen", "script", "sea", "search", "season",
    "seat", "second", "secret", "section", "sector", "secure", "security",
    "see", "seed", "seek", "seem", "select", "self", "sell", "send",
    "senior", "sense", "sentence", "separate", "series", "serious",
    "servant", "serve", "service", "session", "set", "setting", "settle",
    "seven", "several", "severe", "shade", "shadow", "shake", "shall",
    "shame", "shape", "share", "sharp", "she", "sheep", "sheet", "shelf",
    "shell", "shelter", "shift", "shine", "ship", "shirt", "shock", "shoe",
    "shoot", "shop", "shore", "short", "shot", "should", "shoulder", "shout",
    "show", "shut", "sick", "side", "sight", "sign", "signal", "silence",
    "silent", "silver", "similar", "simple", "sing", "single", "sink",
    "sir", "sister", "sit", "site", "situation", "six", "size", "skill",
    "skin", "skirt", "sky", "sleep", "slice", "slide", "slight", "slip",
    "slow", "small", "smart", "smell", "smile", "smoke", "smooth", "snake",
    "snow", "so", "soap", "social", "society", "sock", "soft", "software",
    "soil", "soldier", "solid", "solution", "solve", "some", "somebody",
    "someone", "something", "sometimes", "son", "song", "soon", "sort",
    "sound", "soup", "source", "south", "space", "spare", "speak", "special",
    "specific", "speech", "speed", "spell", "spend", "spirit", "split",
    "spoke", "spoon", "sport", "spot", "spread", "spring", "square", "staff",
    "stage", "stairs", "stand", "standard", "star", "start", "state",
    "station", "stay", "steady", "steal", "steam", "steel", "step", "stick",
    "still", "stock", "stomach", "stone", "stop", "store", "storm", "story",
    "straight", "strange", "stranger", "strategy", "stream", "street",
    "strength", "stretch", "strike", "string", "strip", "stroke", "strong",
    "structure", "student", "studio", "study", "stuff", "stupid", "style",
    "subject", "submit", "subsequent", "substance", "succeed", "success",
    "such", "sudden", "suffer", "sugar", "suggest", "suit", "sum", "summer",
    "sun", "super", "supply", "support", "suppose", "sure", "surface",
    "surprise", "surround", "survey", "survive", "suspect", "swim", "switch",
    "symbol", "system", "table", "tail", "take", "tale", "talk", "tall",
    "tank", "tap", "tape", "target", "task", "taste", "tax", "tea", "teach",
    "teacher", "team", "tear", "telephone", "television", "tell", "temperature",
    "temporary", "ten", "tend", "term", "terms", "terrible", "test", "text",
    "than", "thank", "that", "the", "theater", "their", "them", "theme",
    "then", "theory", "there", "therefore", "these", "they", "thick",
    "thin", "thing", "think", "third", "this", "those", "though", "thought",
    "thousand", "thread", "threat", "three", "throat", "through", "throw",
    "thumb", "thus", "ticket", "tie", "tiger", "tight", "time", "tin",
    "tiny", "tip", "title", "to", "today", "toe", "together", "tomato",
    "tomorrow", "tone", "tongue", "tonight", "too", "tool", "tooth",
    "top", "topic", "total", "touch", "tour", "toward", "tower", "town",
    "track", "trade", "traffic", "trail", "train", "transfer", "transform",
    "translate", "transport", "trap", "travel", "treat", "tree", "trial",
    "tribe", "trick", "trip", "troop", "trouble", "truck", "true", "trust",
    "truth", "try", "tube", "turn", "twelve", "twenty", "twice", "two",
    "type", "uncle", "under", "understand", "uniform", "union", "unit",
    "universe", "university", "unless", "until", "unusual", "up", "upon",
    "upper", "upset", "urban", "urge", "us", "use", "used", "useful",
    "user", "usual", "usually", "value", "variety", "various", "vast",
    "vegetable", "vehicle", "venture", "version", "very", "vessel",
    "veteran", "via", "victim", "victory", "view", "village", "violence",
    "virtue", "virus", "visit", "visitor", "visual", "voice", "volume",
    "vote", "wage", "wait", "wake", "walk", "wall", "wander", "want",
    "war", "warm", "warn", "wash", "watch", "water", "wave", "way",
    "we", "weak", "wealth", "weapon", "wear", "weather", "web", "wedding",
    "week", "weigh", "weight", "welcome", "well", "west", "wet", "what",
    "wheel", "when", "where", "whether", "which", "while", "white", "who",
    "whole", "whom", "whose", "why", "wide", "wife", "wild", "will",
    "win", "wind", "window", "wine", "wing", "winner", "winter", "wire",
    "wise", "wish", "with", "within", "without", "woman", "wonder", "wood",
    "word", "work", "worker", "working", "world", "worry", "worth", "would",
    "wrap", "write", "writer", "writing", "wrong", "yard", "year", "yellow",
    "yes", "yesterday", "yet", "you", "young", "your", "youth",
}


def dale_chall(text):
    """
    Dale-Chall Readability Formula.
    Raw score = 0.1579 * (difficult words / 100 words) + 0.0496 * (words / sentences)
    Grade level = raw score + 3.6365 if raw score > 5, else raw score.
    """
    stats = get_text_stats(text)
    words = stats["words"]
    sentences = stats["sentences"]
    if words == 0:
        return {"score": 0.0, "grade": "N/A", "label": "No text"}

    word_list = re.findall(r"\b[a-zA-Z][a-zA-Z'-]+\b", text.lower())
    difficult = sum(1 for w in word_list if w not in DALE_CHALL_COMMON_WORDS)
    difficult_pct = difficult / words * 100

    raw = 0.1579 * difficult_pct + 0.0496 * (words / sentences)
    grade = raw + 3.6365 if raw > 5 else raw

    return {
        "score": round(raw, 2),
        "grade": round(grade, 1),
        "label": _grade_label(round(grade)),
        "difficult_words": difficult,
        "difficult_pct": round(difficult_pct, 1),
    }


def forecast(text):
    """
    FORCAST: R = 20 - (N / 10) where N = monosyllabic words in a 150-word sample.
    Designed for technical/military text, bullet points, fragments.
    """
    stats = get_text_stats(text)
    words = stats["words"]
    if words == 0:
        return {"score": 0.0, "grade": "N/A", "label": "No text"}

    mono_pct = stats["monosyllabic"] / words * 150  # scale to 150-word sample
    score = 20 - (mono_pct / 10)
    # Clamp to reasonable range
    score = max(0, min(20, score))
    return {
        "score": round(score, 1),
        "grade": round(score),
        "label": _grade_label(round(score)),
    }


def pmose_ikirsch(text):
    """
    PMOSE/IKIRSCH readability for forms and tables.
    Based on syllables per 100 words and sentence structure.
    Simplified implementation focusing on syllable density.
    """
    stats = get_text_stats(text)
    words = stats["words"]
    if words == 0:
        return {"score": 0.0, "grade": "N/A", "label": "No text"}

    syllables_per_100 = stats["syllables"] / words * 100
    words_per_sentence = words / stats["sentences"]

    # PMOSE/IKIRSCH simplified formula
    score = 0.4 * syllables_per_100 + 0.6 * words_per_sentence - 10
    score = max(0, min(20, score))
    return {
        "score": round(score, 1),
        "grade": round(score),
        "label": _grade_label(round(score)),
    }


def chinese_readability_note():
    """Reference note for Chinese readability (ALTA2022Readability)."""
    return {
        "note": "Chinese readability (ALTA2022Readability) requires character-level analysis "
                "and a reference corpus. See https://github.com/hhlim333/ALTA2022Readability",
    }


# ---------------------------------------------------------------------------
# Scan vault notes
# ---------------------------------------------------------------------------
def scan_readability(vault_dir, days=30):
    """Scan vault notes and compute readability metrics for each."""
    results = []
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)

    for full, rel, name, content in walk_md(vault_dir):
        try:
            mtime = os.path.getmtime(full)
            mtime_dt = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc)
            if mtime_dt < cutoff:
                continue
        except Exception:
            pass

        text = content
        if not text.strip():
            continue

        cl = coleman_liau_index(text)
        dc = dale_chall(text)
        fc = forecast(text)
        pm = pmose_ikirsch(text)

        results.append({
            "path": rel,
            "name": name,
            "words": get_text_stats(text)["words"],
            "coleman_liau": cl,
            "dale_chall": dc,
            "forecast": fc,
            "pmose_ikirsch": pm,
        })

    # Sort by average grade (hardest first)
    def avg_grade(r):
        grades = [
            r["coleman_liau"]["grade"] if isinstance(r["coleman_liau"]["grade"], int) else 0,
            r["dale_chall"]["grade"] if isinstance(r["dale_chall"]["grade"], (int, float)) else 0,
            r["forecast"]["grade"] if isinstance(r["forecast"]["grade"], int) else 0,
            r["pmose_ikirsch"]["grade"] if isinstance(r["pmose_ikirsch"]["grade"], int) else 0,
        ]
        return sum(grades) / len(grades) if grades else 0

    results.sort(key=avg_grade, reverse=True)
    return results


# ---------------------------------------------------------------------------
# Markdown report
# ---------------------------------------------------------------------------
def readability_to_markdown(results, days=30):
    """Render readability results to markdown."""
    lines = [
        f"# Readability Metrics Report",
        f"Generated: {datetime.datetime.now().isoformat()}",
        f"Window: last {days} days",
        f"Notes analyzed: {len(results)}",
        "",
        "---",
        "",
        "## Formulas Used",
        "- **Coleman-Liau**: General writing (letters & sentences per 100 words)",
        "- **Dale-Chall**: Based on difficult-word percentage (common-word list)",
        "- **FORCAST**: Bullet-points, fragments, technical short text",
        "- **PMOSE/IKIRSCH**: Tables, forms, structured content",
        "- **Chinese**: Reference to ALTA2022Readability (see report note)",
        "",
        "---",
        "",
    ]

    if not results:
        lines.append("## No notes found in the specified window.")
        lines.append("")
        lines.append("Run again with different `--days` or check the vault path.")
        return "\n".join(lines)

    lines.append("## Readability Results (hardest first)")
    lines.append("")
    lines.append("| Path | Words | C-L | Dale-Chall | FORCAST | PMOSE/IKIRSCH |")
    lines.append("|------|-------|-----|------------|---------|---------------|")
    for r in results[:30]:
        lines.append(
            f"| `{r['path']}` | {r['words']} | "
            f"{r['coleman_liau']['score']} | {r['dale_chall']['score']} | "
            f"{r['forecast']['score']} | {r['pmose_ikirsch']['score']} |"
        )
    if len(results) > 30:
        lines.append(f"| ... and {len(results) - 30} more notes | | | | | |")
    lines.append("")

    lines.append("## Grade Distribution")
    lines.append("")
    easy = sum(1 for r in results if r["coleman_liau"]["grade"] <= 5)
    medium = sum(1 for r in results if 5 < r["coleman_liau"]["grade"] <= 9)
    hard = sum(1 for r in results if r["coleman_liau"]["grade"] > 9)
    lines.append(f"- **Easy** (≤ grade 5): {easy} notes")
    lines.append(f"- **Medium** (grade 6–9): {medium} notes")
    lines.append(f"- **Hard** (> grade 9): {hard} notes")
    lines.append("")

    lines.append("## Chinese Readability Note")
    lines.append("")
    cn = chinese_readability_note()
    lines.append(f"- {cn['note']}")
    lines.append("")

    lines.append("## Next Steps")
    lines.append("")
    lines.append("Review hard-reading notes and consider simplifying sentence structure.")
    lines.append("Run again: `readability.py --vault <path> scan --days 30 --apply`")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
def run_self_test():
    import tempfile
    import shutil

    print("🧪 readability.py Self-Test Suite")
    print("=" * 50)
    passed = 0
    failed = 0

    def check(name, fn):
        nonlocal passed, failed
        try:
            fn()
            print(f"✅ {name}")
            passed += 1
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            failed += 1

    # Test 1: coleman_liau_index
    def test_coleman_liau():
        text = "The cat sat on the mat. It was a warm day."
        result = coleman_liau_index(text)
        assert "score" in result
        assert "grade" in result
        assert "label" in result
        assert isinstance(result["score"], (int, float))
    check("coleman_liau_index computes", test_coleman_liau)

    # Test 2: dale_chall
    def test_dale_chall():
        text = "The cat sat on the mat. It was a warm day."
        result = dale_chall(text)
        assert "score" in result
        assert "grade" in result
        assert "difficult_words" in result
        assert "difficult_pct" in result
    check("dale_chall computes", test_dale_chall)

    # Test 3: forecast
    def test_forecast():
        text = "The cat sat on the mat. It was a warm day."
        result = forecast(text)
        assert "score" in result
        assert "grade" in result
        assert "label" in result
    check("forecast computes", test_forecast)

    # Test 4: pmose_ikirsch
    def test_pmose_ikirsch():
        text = "The cat sat on the mat. It was a warm day."
        result = pmose_ikirsch(text)
        assert "score" in result
        assert "grade" in result
        assert "label" in result
    check("pmose_ikirsch computes", test_pmose_ikirsch)

    print("=" * 50)
    print(f"🎉 Self-tests: {passed} passed, {failed} failed")
    return failed == 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def parse_args():
    parser = argparse.ArgumentParser(
        description="Hermes Brain Readability Metrics — human readability grading for vault notes.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    sub = parser.add_subparsers(dest="command", help="Command to run")
    p_scan = sub.add_parser("scan", help="Scan vault notes for readability (dry-run report)")
    p_scan.add_argument("--days", type=int, default=30, help="Days of notes to scan (default: 30)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Report only (default)")
    parser.add_argument("--apply", action="store_true", help="Write readability report to vault (overrides --dry-run)")
    parser.add_argument("--test", action="store_true", help="Run built-in self-test suite")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.test:
        ok = run_self_test()
        sys.exit(0 if ok else 1)

    if not args.vault:
        args.vault = os.environ.get("HERMES_VAULT_PATH")
    if not args.vault:
        print("Error: --vault <path> or HERMES_VAULT_PATH is required.", file=sys.stderr)
        sys.exit(1)

    init_paths(args.vault)
    dry_run = not args.apply

    if not os.path.isdir(VAULT):
        print(f"Error: Vault not found at {VAULT}", file=sys.stderr)
        sys.exit(1)

    if args.command != "scan":
        print(f"Error: Unknown command '{args.command}'. Use 'scan'.", file=sys.stderr)
        sys.exit(1)

    print(f"🔍 Scanning vault readability (last {args.days} days)...\n")

    results = scan_readability(VAULT, days=args.days)
    report = readability_to_markdown(results, days=args.days)
    print(report)

    if dry_run:
        print(f"\n📄 Run with --apply to write readability report to {READABILITY_DIR}/")
    else:
        os.makedirs(READABILITY_DIR, exist_ok=True)
        date_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        path = os.path.join(READABILITY_DIR, f"Readability-{date_str}.md")
        write_file(path, report)
        print(f"\n📄 Readability report written to {path}")


if __name__ == "__main__":
    main()
