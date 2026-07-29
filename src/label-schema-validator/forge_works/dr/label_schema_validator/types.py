from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ValidationError:
    code: str
    message: str
    field_path: str = ""


@dataclass(frozen=True)
class ValidationWarning:
    code: str
    message: str
    field_path: str = ""


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    errors: tuple[ValidationError, ...] = ()
    warnings: tuple[ValidationWarning, ...] = ()
    library_version: str = ""
    contract_revision: str = ""


@dataclass(frozen=True)
class ValidatorConfig:
    label_delay_warning_threshold: str | None = None
    intervention_ids_soft_bound: int = 10


@dataclass(frozen=True)
class CatalogEntry:
    estimand_id: str
    outcome_vocabulary: tuple[str, ...]
    version: str
    owner: str
    superseded_by: str | None = None
    notes: str = ""


@dataclass(frozen=True)
class EstimandCatalog:
    entries: dict[str, CatalogEntry] = field(default_factory=dict)

    def lookup(self, estimand_id: str) -> CatalogEntry | None:
        return self.entries.get(estimand_id)
