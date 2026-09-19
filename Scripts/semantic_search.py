#!/usr/bin/env python3
"""
Hermes Brain — Semantic Search Layer

Builds a vector search index over the vault's session and knowledge files,
enabling natural-language queries via a DataviewJS Dashboard widget and
an optional `hermes brain search` command.

Design goals:
- Pure Python, runs locally (no external API calls).
- Lightweight: uses `sentence-transformers/all-MiniLM-L6-v2` (22 MB, CPU-friendly).
- Incremental: only re-embeds new/changed files since last run.
- Stores index + metadata in `.semantic-search/` under the vault root.
- Exposes a simple `search(query, top_k=5)` function for the Dashboard.

Usage:
    python Scripts/semantic_search.py --build      # full rebuild
    python Scripts/semantic_search.py --update     # incremental update
    python Scripts/semantic_search.py --search "prompt optimization" --top 5
    python Scripts/semantic_search.py --serve      # run as a tiny HTTP endpoint for DataviewJS
"""
import argparse
import hashlib
import json
import os
import pickle
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Third-party imports (lazy-loaded to keep startup fast if not used)
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError:
    SentenceTransformer = None
    np = None


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Semantic search for Hermes Brain vault")
    parser.add_argument("--build", action="store_true", help="Full rebuild of the index")
    parser.add_argument("--update", action="store_true", help="Incremental update (default)")
    parser.add_argument("--search", type=str, help="Search query to test")
    parser.add_argument("--top", type=int, default=5, help="Number of results to return")
    parser.add_argument("--serve", action="store_true", help="Run HTTP server for DataviewJS")
    parser.add_argument("--port", type=int, default=8765, help="Port for HTTP server")
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Check VAULT after parsing (so --help works without it)
    VAULT = os.environ.get("HERMES_VAULT_PATH")
    if not VAULT:
        print("HERMES_VAULT_PATH is not set — aborting.")
        sys.exit(1)

    VAULT_PATH = Path(VAULT)
    INDEX_DIR = VAULT_PATH / ".semantic-search"
    INDEX_DIR.mkdir(exist_ok=True)

    INDEX_FILE = INDEX_DIR / "index.npy"
    META_FILE = INDEX_DIR / "metadata.json"
    HASH_FILE = INDEX_DIR / "file_hashes.json"
    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    # Files/folders to index
    INCLUDE_DIRS = [
        "Daily",
        "Memory-Review",
        "Projects",
        "Research",
        "Skills-Notes",
        "MEMORY.md",
        "USER.md",
        "User-Profile.md",
    ]

    # Skip these patterns
    EXCLUDE_PATTERNS = [
        ".git",
        ".obsidian",
        ".smart-env",
        "__pycache__",
        ".pyc",
        "node_modules",
        ".semantic-search",
        "manifest.jsonl",
        "Token-Usage.log",
        "Vault-Audit-Report.md",
        "Agent-Performance.md",
        "Skill-to-Chat-Links.md",
        "Consolidation-Log.md",
        "Promotion-Candidates.md",
    ]


    def should_index(path: Path) -> bool:
        """Check if a file should be indexed."""
        rel = str(path.relative_to(VAULT_PATH)).replace("\\", "/")
        # Skip excluded patterns
        for pat in EXCLUDE_PATTERNS:
            if pat in rel:
                return False
        # Only index markdown files and known knowledge files
        if path.suffix.lower() not in (".md", ".mdx"):
            return False
        # Must be under one of the include dirs
        for inc in INCLUDE_DIRS:
            if rel == inc or rel.startswith(inc + "/"):
                return True
        return False


    def get_file_hash(path: Path) -> str:
        """Return SHA256 hash of file content."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            h.update(f.read())
        return h.hexdigest()


    def chunk_text(text: str, max_chars: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks for better retrieval."""
        if len(text) <= max_chars:
            return [text]
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + max_chars, len(text))
            # Try to break at a sentence boundary
            chunk = text[start:end]
            if end < len(text):
                # Look for last period/question/exclamation
                for sep in [". ", "? ", "! ", "\n\n"]:
                    idx = chunk.rfind(sep)
                    if idx > max_chars // 2:
                        end = start + idx + len(sep)
                        chunk = text[start:end]
                        break
            chunks.append(chunk)
            start = end - overlap
            if start <= 0:
                start = end
        return chunks


    def load_existing_index() -> Tuple[Optional[np.ndarray], List[Dict], Dict[str, str]]:
        """Load existing index, metadata, and file hashes."""
        embeddings = None
        metadata = []
        file_hashes = {}

        if INDEX_FILE.exists():
            embeddings = np.load(INDEX_FILE)
        if META_FILE.exists():
            with open(META_FILE, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        if HASH_FILE.exists():
            with open(HASH_FILE, "r", encoding="utf-8") as f:
                file_hashes = json.load(f)
        return embeddings, metadata, file_hashes


    def save_index(embeddings: np.ndarray, metadata: List[Dict], file_hashes: Dict[str, str]):
        """Save index, metadata, and file hashes."""
        np.save(INDEX_FILE, embeddings)
        with open(META_FILE, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        with open(HASH_FILE, "w", encoding="utf-8") as f:
            json.dump(file_hashes, f, ensure_ascii=False, indent=2)


    def collect_files() -> List[Path]:
        """Collect all files that should be indexed."""
        files = []
        for inc in INCLUDE_DIRS:
            p = VAULT_PATH / inc
            if p.is_file():
                files.append(p)
            elif p.is_dir():
                files.extend(p.rglob("*.md"))
        # Filter by should_index
        return [f for f in files if should_index(f)]


    def build_index(force: bool = False) -> Tuple[np.ndarray, List[Dict]]:
        """Build or update the search index."""
        if SentenceTransformer is None or np is None:
            raise RuntimeError(
                "sentence-transformers and numpy are required. "
                "Install with: pip install sentence-transformers numpy"
            )

        print("Loading model...")
        model = SentenceTransformer(MODEL_NAME)

        # Load existing state
        old_embeddings, old_metadata, old_hashes = load_existing_index()
        old_hash_map = old_hashes

        # Collect current files
        current_files = collect_files()
        print(f"Found {len(current_files)} files to consider")

        # Determine which files need (re)embedding
        new_chunks = []
        new_meta = []
        new_hashes = {}

        for fpath in current_files:
            rel = str(fpath.relative_to(VAULT_PATH)).replace("\\", "/")
            current_hash = get_file_hash(fpath)
            new_hashes[rel] = current_hash

            if not force and rel in old_hash_map and old_hash_map[rel] == current_hash:
                # File unchanged, keep its chunks
                continue

            # File is new or changed - read and chunk
            try:
                content = fpath.read_text(encoding="utf-8")
            except Exception as e:
                print(f"  Warning: Could not read {rel}: {e}")
                continue

            # Strip frontmatter if present
            if content.startswith("---\n"):
                parts = content.split("---\n", 2)
                if len(parts) >= 3:
                    content = parts[2]

            chunks = chunk_text(content)
            for i, chunk in enumerate(chunks):
                new_chunks.append(chunk)
                new_meta.append({
                    "file": rel,
                    "chunk": i,
                    "text": chunk[:500],  # Store preview for results
                })

        if new_chunks:
            print(f"Embedding {len(new_chunks)} new/updated chunks...")
            new_embeddings = model.encode(new_chunks, show_progress_bar=True, convert_to_numpy=True)
        else:
            print("No new or changed files to embed.")
            new_embeddings = np.array([]).reshape(0, 384)  # 384 is MiniLM-L6-v2 dim

        # Merge with unchanged old embeddings
        if old_embeddings is not None and len(old_embeddings) > 0:
            # Filter old metadata to keep only files that are still current and unchanged
            kept_meta = []
            kept_embs = []
            for i, m in enumerate(old_metadata):
                rel = m["file"]
                if rel in new_hashes and new_hashes[rel] == old_hash_map.get(rel):
                    kept_meta.append(m)
                    kept_embs.append(old_embeddings[i])

            if kept_embs:
                all_embeddings = np.vstack([np.array(kept_embs), new_embeddings])
                all_metadata = kept_meta + new_meta
            else:
                all_embeddings = new_embeddings
                all_metadata = new_meta
        else:
            all_embeddings = new_embeddings
            all_metadata = new_meta

        # Save
        save_index(all_embeddings, all_metadata, new_hashes)
        print(f"Index saved: {len(all_embeddings)} chunks from {len(new_hashes)} files")
        return all_embeddings, all_metadata


    def search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search the index for a query string."""
        if SentenceTransformer is None or np is None:
            raise RuntimeError(
                "sentence-transformers and numpy are required. "
                "Install with: pip install sentence-transformers numpy"
            )

        embeddings, metadata = load_existing_index()
        if embeddings is None or len(embeddings) == 0:
            return []

        model = SentenceTransformer(MODEL_NAME)
        query_emb = model.encode([query], convert_to_numpy=True)[0]

        # Cosine similarity
        norms = np.linalg.norm(embeddings, axis=1)
        query_norm = np.linalg.norm(query_emb)
        if query_norm == 0:
            return []
        sims = embeddings @ query_emb / (norms * query_norm + 1e-8)

        # Top k
        top_indices = np.argsort(sims)[::-1][:top_k]
        results = []
        for idx in top_indices:
            m = metadata[idx]
            results.append({
                "file": m["file"],
                "chunk": m["chunk"],
                "text": m["text"],
                "score": float(sims[idx]),
            })
        return results


    def serve(port: int = 8765):
        """Run a tiny HTTP server for DataviewJS to query."""
        try:
            from http.server import HTTPServer, BaseHTTPRequestHandler
            import urllib.parse
        except ImportError:
            print("http.server not available")
            return

        class SearchHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                if parsed.path == "/search":
                    params = urllib.parse.parse_qs(parsed.query)
                    q = params.get("q", [""])[0]
                    k = int(params.get("k", ["5"])[0])
                    results = search(q, top_k=k)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps({"results": results}).encode())
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, format, *args):
                pass  # Suppress default log

        server = HTTPServer(("localhost", port), SearchHandler)
        print(f"Semantic search server running on http://localhost:{port}/search?q=...")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down...")
            server.shutdown()

    if args.build:
        build_index(force=True)
    elif args.update or (not args.search and not args.serve):
        build_index(force=False)
    elif args.search:
        if not INDEX_FILE.exists():
            print("Index not found. Run with --build first.")
            return
        results = search(args.search, top_k=args.top)
        if not results:
            print("No results found.")
        else:
            for i, r in enumerate(results, 1):
                print(f"\n{i}. [{r['score']:.3f}] {r['file']} (chunk {r['chunk']})")
                print(f"   {r['text'][:200]}...")
    elif args.serve:
        serve(args.port)


if __name__ == "__main__":
    main()