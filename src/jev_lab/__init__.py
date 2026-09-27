"""A minimal, auditable bench for measuring TypeSafe Jev behaviour locally.

The lab answers three questions with local evidence rather than vendor claims: what Jev can do,
what the documented limits look like in practice, and what each call actually costs in tokens,
latency, and dollars. Every real API call appends one line to ``results/usage.jsonl``.

Ground rules:
    - Official TypeSafe docs are the source of truth for product semantics.
    - Official claims and local measurements are recorded separately.
    - Code does arithmetic; Jev makes semantic judgments.
"""

__all__ = ["__version__"]

# The version lifecycle, matching `pyproject.toml`: `0.1.0` is the frozen evidence release tagged
# `v0.1.0` (and that tag carries its own copy of this file); `0.1.1.dev0` is post-freeze
# development identity. See `pyproject.toml` for the full reading.
__version__ = "0.1.1.dev0"
