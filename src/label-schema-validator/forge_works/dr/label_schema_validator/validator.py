from __future__ import annotations

from typing import TYPE_CHECKING, Any

from forge_works.dr.label_schema_validator.rules import (
    check_cross_field,
    check_provenance,
    check_required_fields,
    collect_unknown_field_warnings,
    collect_warnings,
)
from forge_works.dr.label_schema_validator.types import (
    ValidationResult,
    ValidatorConfig,
)

if TYPE_CHECKING:
    from forge_works.dr.label_schema_validator.types import EstimandCatalog

LIBRARY_VERSION = "0.1.0"
CONTRACT_REVISION = "v1"


def validate_label_event(
    event: dict[str, Any],
    estimand_catalog: EstimandCatalog | None = None,
    config: ValidatorConfig | None = None,
) -> ValidationResult:
    active_config = config if config is not None else ValidatorConfig()

    errors: list = []
    errors.extend(check_required_fields(event, estimand_catalog))
    errors.extend(check_provenance(event))
    errors.extend(check_cross_field(event))

    warnings: list = []
    warnings.extend(collect_warnings(event, active_config, estimand_catalog))
    warnings.extend(collect_unknown_field_warnings(event))

    return ValidationResult(
        is_valid=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
        library_version=LIBRARY_VERSION,
        contract_revision=CONTRACT_REVISION,
    )
