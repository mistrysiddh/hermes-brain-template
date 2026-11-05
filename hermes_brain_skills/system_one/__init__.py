"""Hermes Brain — System One Memory Operating System.

Local System One Memory OS & Multi-Agent Second Brain per mem-draft-spec.txt.

Architecture:
- Capture → Immutable Ledger → Derived Layer → System One → System Two → Delivery → Lifecycle
- Hierarchical agentic memory (working / session / long-term hot-warm-cold)
- System One Decision Layer: Boolean / Choice / Score primitives
- Multi-harness compliant: --vault, --dry-run default, --apply, stdlib-only, --test

All raw evidence is append-only and immutable. Derived views are fully rebuildable.
No silent model rewrite of source of truth. Non-destructive evolution only.
"""

__version__ = "0.1.0"

from hermes_brain_skills.system_one import invariants
from hermes_brain_skills.system_one import storage
from hermes_brain_skills.system_one import models
from hermes_brain_skills.system_one import decision_layer

__all__ = [
    "invariants",
    "storage",
    "models",
    "decision_layer",
    "__version__",
]
