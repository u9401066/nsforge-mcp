"""
Derivation Results Repository

This module manages DERIVED formulas - new formulas created through
verified derivation processes, NOT basic formulas from textbooks.

What belongs here:
✅ Temperature-corrected drug elimination models
✅ Body fat-adjusted distribution models
✅ Renal function-adjusted dosing formulas
✅ Custom PK/PD models for specific drugs
✅ Any formula derived and verified through NSForge

What does NOT belong here:
❌ Basic physics (F=ma) → Use sympy-mcp
❌ Standard constants → Use sympy-mcp
❌ Clinical scores (APACHE) → Use medical-calc-mcp
❌ Textbook formulas → Already in sympy

The "Forge" in NSForge means we CREATE new formulas through derivation.
"""

import contextlib
import copy
import os
import tempfile
import threading
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from sympy import Basic

from nsforge.infrastructure.parsing import parse_expression_safe
from nsforge.infrastructure.storage_paths import contained_path, validate_storage_segment


@dataclass
class DerivationResult:
    """
    A formula that was derived and verified through NSForge.

    This represents the OUTPUT of a derivation process, not a textbook formula.
    """

    # Identification
    id: str
    name: str
    expression: str  # SymPy expression string
    version: str = "1.0.0"
    variables: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Derivation provenance
    derived_from: list[str] = field(default_factory=list)  # Base formulas used
    derivation_steps: list[str] = field(default_factory=list)  # Step descriptions
    assumptions: list[str] = field(default_factory=list)

    # Verification status
    verified: bool = False
    verification_method: str = ""  # e.g., "reverse_derivative", "dimensional_analysis"
    verified_at: str | None = None
    # Compatibility metadata may still be caller asserted.  Strict workflows
    # only trust immutable VerificationEvidence from the run store.
    verification_trust: str = "none"

    # Metadata
    category: str = ""
    tags: list[str] = field(default_factory=list)
    description: str = ""
    clinical_context: str = ""  # When to use this formula
    limitations: list[str] = field(default_factory=list)

    # References
    references: list[str] = field(default_factory=list)
    author: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_sympy(self) -> Basic:
        """Convert expression string to SymPy expression."""
        parsed, error = parse_expression_safe(self.expression)
        if error is not None or not isinstance(parsed, Basic):
            raise ValueError(error or "persisted expression is not a scalar SymPy value")
        return parsed

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "expression": self.expression,
            "variables": self.variables,
            "derived_from": self.derived_from,
            "derivation_steps": self.derivation_steps,
            "assumptions": self.assumptions,
            "verified": self.verified,
            "verification_method": self.verification_method,
            "verified_at": self.verified_at,
            "verification_trust": self.verification_trust,
            "category": self.category,
            "tags": self.tags,
            "description": self.description,
            "clinical_context": self.clinical_context,
            "limitations": self.limitations,
            "references": self.references,
            "author": self.author,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DerivationResult":
        """Create from dictionary."""
        return cls(**data)

    @classmethod
    def from_yaml(cls, yaml_str: str) -> "DerivationResult":
        """Create from YAML string."""
        data = yaml.safe_load(yaml_str)
        return cls.from_dict(data)


class DerivationRepository:
    """
    Repository for storing and retrieving derived formulas.

    Derivation results can be:
    1. Registered programmatically during a session
    2. Loaded from YAML files in formulas/ directory
    3. Saved for future reuse
    """

    def __init__(self, formulas_dir: Path | None = None):
        self._results: dict[str, DerivationResult] = {}
        self._formulas_dir = formulas_dir
        self._lock = threading.RLock()

        if formulas_dir and formulas_dir.exists():
            self._load_from_directory(formulas_dir)

    @contextlib.contextmanager
    def transaction(self) -> Iterator[None]:
        """Hold the repository lock across a compound tool-layer operation."""
        with self._lock:
            yield

    def _load_from_directory(self, directory: Path) -> None:
        """Load derivation results from YAML files."""
        with self._lock:
            for yaml_file in directory.rglob("*.yaml"):
                try:
                    with open(yaml_file, encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                        if data and "id" in data:
                            result = DerivationResult.from_dict(data)
                            self._results[result.id] = result
                except Exception:
                    pass  # Skip invalid files

    def register(self, result: DerivationResult) -> None:
        """Register a new derivation result."""
        with self._lock:
            self._results[result.id] = result

    def get(self, result_id: str) -> DerivationResult | None:
        """Get a derivation result by ID."""
        with self._lock:
            return self._results.get(result_id)

    def snapshot(self, result_id: str) -> dict[str, Any] | None:
        """Return a detached result snapshot safe for concurrent serialization."""
        with self._lock:
            result = self._results.get(result_id)
            return copy.deepcopy(result.to_dict()) if result is not None else None

    def list_all(self, category: str | None = None) -> list[str]:
        """List all derivation result IDs."""
        with self._lock:
            if category is None:
                return list(self._results.keys())
            return [rid for rid, r in self._results.items() if r.category == category]

    def search(self, query: str) -> list[DerivationResult]:
        """Search derivation results by keyword."""
        with self._lock:
            results = []
            query_lower = query.lower()
            for result in self._results.values():
                if (
                    query_lower in result.name.lower()
                    or query_lower in result.description.lower()
                    or any(query_lower in tag.lower() for tag in result.tags)
                ):
                    results.append(result)
            return results

    def search_snapshots(self, query: str) -> list[dict[str, Any]]:
        """Search and detach matching results under one repository lock."""
        with self._lock:
            return [copy.deepcopy(result.to_dict()) for result in self.search(query)]

    def save(self, result_id: str, directory: Path | None = None) -> Path:
        """Save a derivation result to YAML file."""
        with self._lock:
            result = self._results.get(result_id)
            if result is None:
                raise ValueError(f"Derivation result '{result_id}' not found")

            save_dir = directory or self._formulas_dir
            if save_dir is None:
                raise ValueError("No directory specified for saving")

            safe_id = validate_storage_segment(result.id, field="result id")
            resolved_root = save_dir.resolve()
            # Category is metadata, never a caller-controlled path.  Keeping it
            # to one validated segment preserves the legacy directory layout.
            category_dir = resolved_root
            if result.category:
                category = validate_storage_segment(result.category, field="category")
                category_dir = contained_path(resolved_root, category, field="category")
            category_dir.mkdir(parents=True, exist_ok=True)

            # Atomic write: the temporary file must share the destination directory
            # so os.replace is atomic on the target filesystem.
            file_path = contained_path(
                resolved_root,
                category_dir / f"{safe_id}.yaml",
                field="derivation result path",
            )
            tmp_fd, tmp_name = tempfile.mkstemp(
                dir=str(category_dir), prefix=f".{safe_id}_", suffix=".tmp"
            )
            try:
                with open(tmp_fd, "w", encoding="utf-8") as f:
                    yaml.dump(
                        result.to_dict(),
                        f,
                        default_flow_style=False,
                        allow_unicode=True,
                    )
                os.replace(tmp_name, file_path)
            except BaseException:
                with contextlib.suppress(OSError):
                    os.unlink(tmp_name)
                raise

            return file_path

    def register_and_save(
        self,
        result: DerivationResult,
        directory: Path | None = None,
    ) -> Path:
        """Register and persist a result atomically from the caller's view."""
        with self._lock:
            previous = self._results.get(result.id)
            self._results[result.id] = result
            try:
                return self.save(result.id, directory)
            except BaseException:
                if previous is None:
                    self._results.pop(result.id, None)
                else:
                    self._results[result.id] = previous
                raise

    def update_and_save(
        self,
        result_id: str,
        *,
        directory: Path | None = None,
        **updates: Any,
    ) -> Path:
        """Apply metadata and persistence as one rollback-capable operation."""
        with self._lock:
            current = self._results.get(result_id)
            if current is None:
                raise ValueError(f"Derivation result '{result_id}' not found")
            previous = copy.deepcopy(current)
            save_dir = directory or self._formulas_dir
            old_path: Path | None = None
            if save_dir is not None:
                safe_id = validate_storage_segment(previous.id, field="result id")
                old_parent = save_dir.resolve()
                if previous.category:
                    old_category = validate_storage_segment(previous.category, field="category")
                    old_parent = contained_path(old_parent, old_category, field="category")
                old_path = contained_path(
                    save_dir.resolve(),
                    old_parent / f"{safe_id}.yaml",
                    field="derivation result path",
                )
            try:
                self.update(result_id, **updates)
                new_path = self.save(result_id, directory)
            except BaseException:
                self._results[result_id] = previous
                raise
            if old_path is not None and old_path != new_path and old_path.exists():
                old_path.unlink()
            return new_path

    def update(
        self,
        result_id: str,
        **updates: Any,
    ) -> DerivationResult:
        """
        Update a derivation result's metadata.

        Args:
            result_id: The ID of the derivation result to update
            **updates: Fields to update (description, clinical_context, tags, etc.)

        Returns:
            Updated DerivationResult

        Raises:
            ValueError: If result_id not found
        """
        with self._lock:
            result = self._results.get(result_id)
            if result is None:
                raise ValueError(f"Derivation result '{result_id}' not found")

            # Update allowed fields
            allowed_fields = {
                "name",
                "description",
                "clinical_context",
                "assumptions",
                "limitations",
                "references",
                "tags",
                "category",
                "version",
                "verified",
                "verification_method",
                "verified_at",
            }

            for key, value in updates.items():
                if key in allowed_fields and hasattr(result, key):
                    if key == "category" and value:
                        validate_storage_segment(str(value), field="category")
                    setattr(result, key, value)
                    if key == "verified":
                        # This legacy repository API has no verifier attestation;
                        # record the assertion but never promote it to trusted.
                        result.verification_trust = "caller_asserted" if value else "none"

            return result

    def delete(self, result_id: str, delete_file: bool = True) -> bool:
        """
        Delete a derivation result.

        Args:
            result_id: The ID of the derivation result to delete
            delete_file: Whether to delete the YAML file (default: True)

        Returns:
            True if deleted, False if not found
        """
        with self._lock:
            result = self._results.get(result_id)
            if result is None:
                return False

            file_path: Path | None = None
            if delete_file and self._formulas_dir:
                safe_id = validate_storage_segment(result_id, field="result id")
                root = self._formulas_dir.resolve()
                category_dir = root
                if result.category:
                    category = validate_storage_segment(result.category, field="category")
                    category_dir = contained_path(root, category, field="category")
                file_path = contained_path(
                    root,
                    category_dir / f"{safe_id}.yaml",
                    field="derivation result path",
                )

            # Resolve and validate every filesystem target before mutating the
            # in-memory index.  A rejected path therefore cannot cause a
            # partial delete.
            del self._results[result_id]
            if file_path is not None and file_path.exists():
                file_path.unlink()

            return True

    def stats(self) -> dict[str, Any]:
        """Get repository statistics."""
        with self._lock:
            categories: dict[str, int] = {}
            verified_count = 0

            for result in self._results.values():
                cat = result.category or "uncategorized"
                categories[cat] = categories.get(cat, 0) + 1
                if result.verified:
                    verified_count += 1

            return {
                "total": len(self._results),
                "verified": verified_count,
                "unverified": len(self._results) - verified_count,
                "categories": categories,
            }


# Global repository instance
_repository: DerivationRepository | None = None
_repository_lock = threading.Lock()


def get_repository(formulas_dir: Path | None = None) -> DerivationRepository:
    """Get the global derivation repository instance."""
    global _repository
    if _repository is None:
        with _repository_lock:
            if _repository is None:
                _repository = DerivationRepository(formulas_dir)
    return _repository
