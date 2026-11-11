import os, sys, json, numpy as np
from sentence_transformers import SentenceTransformer
import argparse


# ---------------------------------------------------------------------------
# Path resolution — deferred to main(), never at module level
# ---------------------------------------------------------------------------
VAULT = None


def init_paths(vault_path):
    global VAULT
    VAULT = os.path.abspath(vault_path)


def parse_args():
    parser = argparse.ArgumentParser(
        description="trend_digest.py — multi-harness compatible.",
    )
    parser.add_argument("--vault", help="Path to the Hermes Brain vault root")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Report only, no changes (default)")
    parser.add_argument("--apply", action="store_true",
                        help="Apply safe auto-fixes (overrides --dry-run)")
    parser.add_argument("--test", action="store_true",
                        help="Run built-in self-test suite")
    return parser.parse_args()



def main(args=None):
    if args is None:
        args = parse_args()

    if not args.vault:
        args.vault = os.environ.get("HERMES_VAULT_PATH")
    if not args.vault:
        print("Error: --vault <path> or HERMES_VAULT_PATH is required.", file=sys.stderr)
        sys.exit(1)

    init_paths(args.vault)
    vault = sys.argv[1]
    query = sys.argv[2]
    top_n = int(sys.argv[3])

    # Collect markdown files
    docs = []
    paths = []
    for root, _, files in os.walk(vault):
        for f in files:
            if f.lower().endswith('.md'):
                full = os.path.join(root, f)
                try:
                    with open(full, 'r', encoding='utf-8', errors='ignore') as fh:
                        text = fh.read()
                        # Strip simple YAML frontmatter
                        if text.startswith('---'):
                            parts = text.split('---', 2)
                            if len(parts) >= 3:
                                text = parts[2]
                        text = text.strip()
                        if not text:
                            continue
                        docs.append(text[:800])  # truncate to keep memory sane
                        paths.append(full)
                except Exception as e:
                    # skip unreadable files
                    pass

    if not docs:
        print(json.dumps([]))
        return

    # Load model (same family as Smart Connections' default)
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    model = SentenceTransformer(model_name)

    # Encode
    doc_emb = model.encode(docs, batch_size=32, show_progress_bar=False, convert_to_numpy=True)
    doc_emb_norm = doc_emb / np.linalg.norm(doc_emb, axis=1, keepdims=True)

    q_emb = model.encode([query], convert_to_numpy=True)[0]
    q_emb_norm = q_emb / np.linalg.norm(q_emb)

    # Cosine similarity
    sims = np.dot(doc_emb_norm, q_emb_norm)
    top_idx = np.argsort(sims)[::-1][:top_n]

    results = []
    for idx in top_idx:
        score = float(sims[idx])
        rel_path = os.path.relpath(paths[idx], vault)
        snippet = docs[idx].replace('\n', ' ')[:220]
        results.append({
            "path": rel_path.replace('\\', '/'),
            "score": round(score, 4),
            "snippet": snippet
        })

    print(json.dumps(results, ensure_ascii=False))

if __name__ == "__main__":
    main(parse_args())