#!/usr/bin/env python3
# template_drift.py
# Compares a user's vault against the latest template to show what's safe to update and what's customized.

import os
import sys
import subprocess
import filecmp
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass

@dataclass
class DriftItem:
    path: str
    status: str  # "safe", "customized", "outdated", "missing"
    template_hash: str = ""
    user_hash: str = ""
    details: str = ""

def get_file_hash(filepath: Path) -> str:
    """Get SHA256 hash of a file."""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()[:12]
    except Exception:
        return ""

def should_ignore(path: Path) -> bool:
    """Check if path should be ignored (personal data, git, etc.)."""
    ignore_patterns = [
        # Personal data directories
        "Daily",
        "Memory-Review",
        "Research",
        ".smart-env",
        ".obsidian/plugins",
        ".obsidian/workspace.json",
        ".obsidian/workspace-mobile.json",
        # Git
        ".git",
        # Template-generated files that users customize
        "User-Profile.md",
        # Temporary files
        "__pycache__",
        "*.pyc",
        "*.tmp",
    ]
    
    path_str = str(path)
    for pattern in ignore_patterns:
        if pattern in path_str:
            return True
    return False

def get_template_files(template_root: Path) -> List[Path]:
    """Get all template files that should be compared."""
    template_files = []
    for root, dirs, files in os.walk(template_root):
        # Skip .git directory
        if '.git' in root:
            continue
        for file in files:
            filepath = Path(root) / file
            rel_path = filepath.relative_to(template_root)
            if not should_ignore(rel_path):
                template_files.append(rel_path)
    return template_files

def compare_vaults(user_vault: Path, template_root: Path) -> List[DriftItem]:
    """Compare user vault against template and return drift items."""
    drift_items = []
    
    # Get template files
    template_files = get_template_files(template_root)
    
    # Create a set of user files for quick lookup
    user_files = set()
    for root, dirs, files in os.walk(user_vault):
        for file in files:
            filepath = Path(root) / file
            rel_path = filepath.relative_to(user_vault)
            if not should_ignore(rel_path):
                user_files.add(rel_path)
    
    # Compare each template file
    for rel_path in template_files:
        template_file = template_root / rel_path
        user_file = user_vault / rel_path
        
        template_hash = get_file_hash(template_file)
        
        if user_file.exists():
            user_hash = get_file_hash(user_file)
            
            if template_hash == user_hash:
                drift_items.append(DriftItem(
                    path=str(rel_path),
                    status="safe",
                    template_hash=template_hash,
                    user_hash=user_hash,
                    details="Identical to template — safe to update"
                ))
            else:
                # Check if it's a known customization point
                if rel_path.name == "User-Profile.md":
                    drift_items.append(DriftItem(
                        path=str(rel_path),
                        status="customized",
                        template_hash=template_hash,
                        user_hash=user_hash,
                        details="Personal profile — will be preserved on update"
                    ))
                else:
                    drift_items.append(DriftItem(
                        path=str(rel_path),
                        status="outdated",
                        template_hash=template_hash,
                        user_hash=user_hash,
                        details="Modified from template — update recommended"
                    ))
        else:
            drift_items.append(DriftItem(
                path=str(rel_path),
                status="missing",
                template_hash=template_hash,
                details="File exists in template but not in your vault"
            ))
    
    # Check for user files not in template (custom additions)
    for rel_path in user_files:
        if rel_path not in template_files:
            user_file = user_vault / rel_path
            user_hash = get_file_hash(user_file)
            drift_items.append(DriftItem(
                path=str(rel_path),
                status="customized",
                user_hash=user_hash,
                details="Custom file not in template — will be preserved"
            ))
    
    return drift_items

def print_drift_report(drift_items: List[DriftItem], user_vault: Path, template_version: str = "unknown"):
    """Print a formatted drift report."""
    
    # Count statuses
    safe_count = sum(1 for item in drift_items if item.status == "safe")
    customized_count = sum(1 for item in drift_items if item.status == "customized")
    outdated_count = sum(1 for item in drift_items if item.status == "outdated")
    missing_count = sum(1 for item in drift_items if item.status == "missing")
    
    total = len(drift_items)
    alignment = (safe_count / total * 100) if total > 0 else 0
    
    print(f"📊 Template Drift Report for {user_vault}")
    print(f"📦 Template version: {template_version}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"📈 Alignment: {alignment:.0f}% ({safe_count}/{total} files match template)")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    if outdated_count > 0:
        print(f"\n❌ Outdated ({outdated_count} files) — Update recommended:")
        for item in drift_items:
            if item.status == "outdated":
                print(f"   ├── {item.path}")
                print(f"   │   Template: {item.template_hash} | Your: {item.user_hash}")
                print(f"   │   {item.details}")
    
    if customized_count > 0:
        print(f"\n⚠️  Customized ({customized_count} files) — Preserve on update:")
        for item in drift_items:
            if item.status == "customized":
                print(f"   ├── {item.path}")
                print(f"   │   {item.details}")
    
    if missing_count > 0:
        print(f"\n📋 Missing ({missing_count} files) — Consider adding:")
        for item in drift_items:
            if item.status == "missing":
                print(f"   ├── {item.path}")
                print(f"   │   {item.details}")
    
    if safe_count > 0:
        print(f"\n✅ Safe to update ({safe_count} files) — Identical to template")
    
    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"💡 Next steps:")
    
    if outdated_count > 0:
        print(f"   Run: ./_System/Scripts/Installers/update.sh --preserve-custom")
        print(f"   (This will update safe/outdated files while preserving customized files)")
    elif customized_count > 0:
        print(f"   Your vault has customizations but no outdated files.")
        print(f"   You're up to date! Run update.sh if you want to pull any new template features.")
    else:
        print(f"   Your vault is perfectly aligned with the template.")
        print(f"   Run update.sh when a new template version is released.")

def get_template_version(template_root: Path) -> str:
    """Try to get template version from VERSION file or git."""
    version_file = template_root / "VERSION"
    if version_file.exists():
        try:
            return version_file.read_text().strip()
        except Exception:
            pass
    
    # Try git describe
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--always"],
            cwd=template_root,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception:
        pass
    
    return "unknown"

def main():
    if len(sys.argv) < 2:
        print("Usage: python template_drift.py <user_vault_path> [--template-root <path>]")
        print("  --template-root: Path to template repo (default: current script's template)")
        sys.exit(1)
    
    user_vault = Path(sys.argv[1]).resolve()
    if not user_vault.exists():
        print(f"❌ User vault not found: {user_vault}")
        sys.exit(1)
    
    # Determine template root
    if "--template-root" in sys.argv:
        idx = sys.argv.index("--template-root")
        if idx + 1 < len(sys.argv):
            template_root = Path(sys.argv[idx + 1]).resolve()
        else:
            print("❌ --template-root requires a path")
            sys.exit(1)
    else:
        # Default: assume script is in template's _System/Scripts/
        script_dir = Path(__file__).resolve().parent
        template_root = script_dir.parent.parent  # Go up from _System/Scripts/ to template root
    
    if not template_root.exists():
        print(f"❌ Template root not found: {template_root}")
        sys.exit(1)
    
    print(f"🔍 Comparing {user_vault} against template at {template_root}")
    print()
    
    template_version = get_template_version(template_root)
    drift_items = compare_vaults(user_vault, template_root)
    print_drift_report(drift_items, user_vault, template_version)

if __name__ == "__main__":
    main()