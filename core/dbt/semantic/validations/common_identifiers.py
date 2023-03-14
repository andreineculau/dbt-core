from typing import Dict, List, Set
from dbt.semantic.references import EntityElementReference, IdentifierReference

from dbt.contracts.graph.nodes import Entity
from dbt.contracts.graph.identifiers import Identifier
from dbt.semantic.user_configured_model import UserConfiguredModel
from dbt.semantic.validations.validator_helpers import (
    EntityElementContext,
    EntityElementType,
    ModelValidationRule,
    ValidationWarning,
    validate_safely,
    ValidationIssueType,
)


class CommonIdentifiersRule(ModelValidationRule):
    """Checks that identifiers exist on more than one entity"""

    @staticmethod
    def _map_entity_identifiers(entities: List[Entity]) -> Dict[IdentifierReference, Set[str]]:
        """Generate mapping of identifier names to the set of entities where it is defined"""
        identifiers_to_entities: Dict[IdentifierReference, Set[str]] = {}
        for entity in entities or []:
            for identifier in entity.identifiers or []:
                if identifier.reference in identifiers_to_entities:
                    identifiers_to_entities[identifier.reference].add(entity.name)
                else:
                    identifiers_to_entities[identifier.reference] = {entity.name}
        return identifiers_to_entities

    @staticmethod
    @validate_safely(whats_being_done="checking identifier exists on more than one entity")
    def _check_identifier(
        identifier: Identifier,
        entity: Entity,
        identifiers_to_entities: Dict[IdentifierReference, Set[str]],
    ) -> List[ValidationIssueType]:
        issues: List[ValidationIssueType] = []
        # If the identifier is the dict and if the set of entitys minus this entity is empty,
        # then we warn the user that their identifier will be unused in joins
        if (
            identifier.reference in identifiers_to_entities
            and len(identifiers_to_entities[identifier.reference].difference({entity.name})) == 0
        ):
            issues.append(
                ValidationWarning(
                    context=EntityElementContext(
                        entity_element=EntityElementReference(
                            entity_name=entity.name, name=identifier.name
                        ),
                        element_type=EntityElementType.IDENTIFIER,
                    ),
                    message=f"Identifier `{identifier.reference.name}` "
                    f"only found in one entity `{entity.name}` "
                    f"which means it will be unused in joins.",
                )
            )
        return issues

    @staticmethod
    @validate_safely(
        whats_being_done="running model validation warning if identifiers are only one one entity"
    )
    def validate_model(model: UserConfiguredModel) -> List[ValidationIssueType]:
        """Issues a warning for any identifier that is associated with only one entity"""
        issues = []

        identifiers_to_entities = CommonIdentifiersRule._map_entity_identifiers(model.entities)
        for entity in model.entities or []:
            for identifier in entity.identifiers or []:
                issues += CommonIdentifiersRule._check_identifier(
                    identifier=identifier,
                    entity=entity,
                    identifiers_to_entities=identifiers_to_entities,
                )

        return issues