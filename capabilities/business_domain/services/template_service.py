
import uuid
from typing import Any

from sqlalchemy import or_, select

from jonex_core.common import get_db_session
from jonex_core.common.exceptions import InvalidParameterError, ResourceNotFoundError

from capabilities.business_domain.models.template import (
    TemplateAttribute,
    TemplateConstraint,
    TemplateObject,
    TemplateRelation,
    TemplateScenario,
)
from capabilities.business_domain.repository import (
    TemplateAttributeRepository,
    TemplateConstraintRepository,
    TemplateDomainRepository,
    TemplateObjectRepository,
    TemplateRelationRepository,
    TemplateScenarioRepository,
)
from capabilities.business_domain.services import _check_tenant


class TemplateService:



    async def list_domains(self, tenant_id: str, offset: int = 0, limit: int = 20) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = TemplateDomainRepository(session)
            items = await repo.list_all(tenant_id, offset, limit)
            total = await repo.count(tenant_id)
            domain_ids = [o.id for o in items]
            scenario_counts: dict[str, int] = {}
            if domain_ids:
                from sqlalchemy import func
                count_rows = await session.execute(
                    select(TemplateScenario.domain_id, func.count(TemplateScenario.id))
                    .where(
                        TemplateScenario.tenant_id == tenant_id,
                        TemplateScenario.is_deleted == 0,
                        TemplateScenario.domain_id.in_(domain_ids),
                    )
                    .group_by(TemplateScenario.domain_id)
                )
                scenario_counts = {row[0]: row[1] for row in count_rows}
            result_items = []
            for o in items:
                d = o.to_dict()
                d["scenario_count"] = scenario_counts.get(o.id, 0)
                result_items.append(d)
            return {"items": result_items, "total": total, "offset": offset, "limit": limit}

    async def get_domain(self, domain_id: str, tenant_id: str) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            obj = await TemplateDomainRepository(session).get_required(domain_id, tenant_id)
            return obj.to_dict()

    async def create_domain(self, tenant_id: str, data: dict) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = TemplateDomainRepository(session)
            obj = await repo.create(
                id=uuid.uuid4().hex,
                tenant_id=tenant_id,
                name=data["name"],
                description=data.get("description"),
                status=data.get("status", "inactive"),
            )
            await session.commit()
            return obj.to_dict()

    async def update_domain(self, domain_id: str, tenant_id: str, data: dict) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = TemplateDomainRepository(session)
            obj = await repo.update(domain_id, tenant_id, **{
                k: v for k, v in data.items()
                if k in ("name", "description", "status") and v is not None
            })
            if obj is None:
                raise ResourceNotFoundError(message=f"Template domain not found: {domain_id}")
            await session.commit()
            return obj.to_dict()

    async def delete_domain(self, domain_id: str, tenant_id: str) -> bool:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = TemplateDomainRepository(session)
            deleted = await repo.delete_soft(domain_id, tenant_id)
            if not deleted:
                raise ResourceNotFoundError(message=f"Template domain not found: {domain_id}")
            await session.commit()
            return True


    async def list_scenarios(
        self,
        tenant_id: str,
        domain_id: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            if domain_id:
                await TemplateDomainRepository(session).get_required(domain_id, tenant_id)
            conditions = [TemplateScenario.domain_id == domain_id] if domain_id else []
            repo = TemplateScenarioRepository(session)
            items = await repo.list_all(tenant_id, offset, limit, extra_conditions=conditions)
            total = await repo.count(tenant_id, extra_conditions=conditions)
            return {"items": [o.to_dict() for o in items], "total": total, "offset": offset, "limit": limit}

    async def create_scenario(self, tenant_id: str, data: dict) -> dict:
        tenant_id = _check_tenant(tenant_id)
        domain_id = data.get("domain_id")
        if not domain_id:
            raise InvalidParameterError(message="A template scenario must be associated with a template domain")

        async with get_db_session() as session:
            await TemplateDomainRepository(session).get_required(domain_id, tenant_id)
            obj = await TemplateScenarioRepository(session).create(
                id=uuid.uuid4().hex,
                tenant_id=tenant_id,
                domain_id=domain_id,
                name=data["name"],
                description=data.get("description"),
                config_json=data.get("config_json", {}),
            )
            await session.commit()
            return obj.to_dict()

    async def get_scenario(self, scenario_id: str, tenant_id: str) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            obj = await TemplateScenarioRepository(session).get_required(scenario_id, tenant_id)
            return obj.to_dict()

    async def update_scenario(self, scenario_id: str, tenant_id: str, data: dict) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = TemplateScenarioRepository(session)
            obj = await repo.get_required(scenario_id, tenant_id)
            old_domain_id = obj.domain_id
            if "domain_id" in data and data["domain_id"] and data["domain_id"] != obj.domain_id:
                await TemplateDomainRepository(session).get_required(data["domain_id"], tenant_id)
            update_values = {
                k: v for k, v in data.items()
                if k in ("name", "description", "domain_id", "config_json") and v is not None
            }
            obj = await repo.update(obj, tenant_id, **update_values)
            if obj.domain_id != old_domain_id:
                object_repo = TemplateObjectRepository(session)
                relation_repo = TemplateRelationRepository(session)
                constraint_repo = TemplateConstraintRepository(session)
                objects = await object_repo.list_all(
                    tenant_id,
                    0,
                    10000,
                    extra_conditions=[TemplateObject.scenario_id == obj.id],
                )
                relations = await relation_repo.list_all(
                    tenant_id,
                    0,
                    10000,
                    extra_conditions=[TemplateRelation.scenario_id == obj.id],
                )
                constraints = await constraint_repo.list_all(
                    tenant_id,
                    0,
                    10000,
                    extra_conditions=[TemplateConstraint.scenario_id == obj.id],
                )
                for template_object in objects:
                    await object_repo.update(template_object, tenant_id, domain_id=obj.domain_id)
                for relation in relations:
                    await relation_repo.update(relation, tenant_id, domain_id=obj.domain_id)
                for constraint in constraints:
                    await constraint_repo.update(constraint, tenant_id, domain_id=obj.domain_id)
            await session.commit()
            return obj.to_dict()

    async def delete_scenario(self, scenario_id: str, tenant_id: str) -> bool:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            scenario_repo = TemplateScenarioRepository(session)
            scenario = await scenario_repo.get_required(scenario_id, tenant_id)
            object_repo = TemplateObjectRepository(session)
            relation_repo = TemplateRelationRepository(session)
            attribute_repo = TemplateAttributeRepository(session)
            constraint_repo = TemplateConstraintRepository(session)

            objects = await object_repo.list_all(
                tenant_id,
                0,
                10000,
                extra_conditions=[TemplateObject.scenario_id == scenario_id],
            )
            relations = await relation_repo.list_all(
                tenant_id,
                0,
                10000,
                extra_conditions=[TemplateRelation.scenario_id == scenario_id],
            )
            constraints = await constraint_repo.list_all(
                tenant_id,
                0,
                10000,
                extra_conditions=[TemplateConstraint.scenario_id == scenario_id],
            )
            for obj in objects:
                attrs = await attribute_repo.list_all(
                    tenant_id,
                    0,
                    10000,
                    extra_conditions=[TemplateAttribute.template_object_id == obj.id],
                )
                for attr in attrs:
                    await attribute_repo.delete_soft(attr, tenant_id)
                await object_repo.delete_soft(obj, tenant_id)
            for relation in relations:
                await relation_repo.delete_soft(relation, tenant_id)
            for constraint in constraints:
                await constraint_repo.delete_soft(constraint, tenant_id)
            await scenario_repo.delete_soft(scenario, tenant_id)
            await session.commit()
            return True


    async def list_objects(self, tenant_id: str, scenario_id: str, offset: int = 0, limit: int = 20) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            scenario = await TemplateScenarioRepository(session).get_required(scenario_id, tenant_id)
            repo = TemplateObjectRepository(session)
            items = await repo.list_all(
                tenant_id,
                offset,
                limit,
                extra_conditions=[TemplateObject.scenario_id == scenario.id],
            )
            total = await repo.count(tenant_id, extra_conditions=[TemplateObject.scenario_id == scenario.id])
            attribute_map = await self._load_attributes(session, tenant_id, [o.id for o in items])
            return {
                "items": [self._object_to_dict(o, attribute_map.get(o.id, [])) for o in items],
                "total": total,
                "offset": offset,
                "limit": limit,
            }

    async def create_object(self, tenant_id: str, scenario_id: str, data: dict) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            scenario = await TemplateScenarioRepository(session).get_required(scenario_id, tenant_id)
            obj = await TemplateObjectRepository(session).create(
                id=uuid.uuid4().hex,
                tenant_id=tenant_id,
                domain_id=scenario.domain_id,
                scenario_id=scenario.id,
                name=data["name"],
                description=data.get("description"),
                status=data.get("status", "draft"),
                ontology_code=data.get("ontology_code"),
                aliases=data.get("aliases", []),
            )
            attrs = await self._replace_attributes(session, tenant_id, obj.id, data.get("attributes", []))
            await session.commit()
            return self._object_to_dict(obj, attrs)

    async def update_object(self, object_id: str, tenant_id: str, data: dict) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            object_repo = TemplateObjectRepository(session)
            obj = await object_repo.get_required(object_id, tenant_id)
            await TemplateScenarioRepository(session).get_required(obj.scenario_id, tenant_id)
            old_name = obj.name
            obj = await object_repo.update(obj, tenant_id, **{
                k: v for k, v in data.items()
                if k in ("name", "description", "status", "ontology_code", "aliases") and v is not None
            })

            new_name = data.get("name")
            if new_name and new_name != old_name:
                await self._sync_constraint_labels_by_target(
                    session, tenant_id, "object", object_id, new_name,
                )
            attrs = await self._load_attributes(session, tenant_id, [obj.id])
            if "attributes" in data:
                attrs[obj.id] = await self._replace_attributes(session, tenant_id, obj.id, data.get("attributes") or [])
            await session.commit()
            return self._object_to_dict(obj, attrs.get(obj.id, []))

    async def delete_object(self, object_id: str, tenant_id: str) -> bool:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            object_repo = TemplateObjectRepository(session)
            attribute_repo = TemplateAttributeRepository(session)
            relation_repo = TemplateRelationRepository(session)
            constraint_repo = TemplateConstraintRepository(session)
            obj = await object_repo.get_required(object_id, tenant_id)

            attrs = await attribute_repo.list_all(
                tenant_id,
                0,
                10000,
                extra_conditions=[TemplateAttribute.template_object_id == obj.id],
            )
            attr_ids = [a.id for a in attrs]
            relations = await relation_repo.list_all(
                tenant_id,
                0,
                10000,
                extra_conditions=[
                    TemplateRelation.scenario_id == obj.scenario_id,
                    or_(
                        TemplateRelation.source_object_id == obj.id,
                        TemplateRelation.target_object_id == obj.id,
                    ),
                ],
            )

            object_constraints = await constraint_repo.list_all(
                tenant_id, 0, 10000,
                extra_conditions=[
                    TemplateConstraint.scenario_id == obj.scenario_id,
                    TemplateConstraint.target_type == "object",
                    TemplateConstraint.target_id == obj.id,
                ],
            )

            attr_constraints: list = []
            if attr_ids:
                attr_constraints = await constraint_repo.list_all(
                    tenant_id, 0, 10000,
                    extra_conditions=[
                        TemplateConstraint.scenario_id == obj.scenario_id,
                        TemplateConstraint.target_type == "attribute",
                        TemplateConstraint.target_id.in_(attr_ids),
                    ],
                )
            for attr in attrs:
                await attribute_repo.delete_soft(attr, tenant_id)
            for relation in relations:
                await relation_repo.delete_soft(relation, tenant_id)
            for constraint in object_constraints + attr_constraints:
                await constraint_repo.delete_soft(constraint, tenant_id)
            await object_repo.delete_soft(obj, tenant_id)
            await session.commit()
            return True


    async def list_relations(self, tenant_id: str, scenario_id: str, offset: int = 0, limit: int = 20) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            scenario = await TemplateScenarioRepository(session).get_required(scenario_id, tenant_id)
            repo = TemplateRelationRepository(session)
            items = await repo.list_all(
                tenant_id,
                offset,
                limit,
                extra_conditions=[TemplateRelation.scenario_id == scenario.id],
            )
            total = await repo.count(tenant_id, extra_conditions=[TemplateRelation.scenario_id == scenario.id])
            object_names = await self._load_object_names(session, tenant_id, scenario.id)
            return {
                "items": [self._relation_to_dict(o, object_names) for o in items],
                "total": total,
                "offset": offset,
                "limit": limit,
            }

    async def create_relation(self, tenant_id: str, scenario_id: str, data: dict) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            scenario = await TemplateScenarioRepository(session).get_required(scenario_id, tenant_id)
            await self._validate_relation_objects(
                session,
                tenant_id,
                scenario.id,
                data.get("source_object_id"),
                data.get("target_object_id"),
            )
            obj = await TemplateRelationRepository(session).create(
                id=uuid.uuid4().hex,
                tenant_id=tenant_id,
                domain_id=scenario.domain_id,
                scenario_id=scenario.id,
                name=data["name"],
                description=data.get("description"),
                source_object_id=data["source_object_id"],
                target_object_id=data["target_object_id"],
                relation_type=data.get("relation_type", "custom"),
                status=data.get("status", "draft"),
                ontology_code=data.get("ontology_code"),
                aliases=data.get("aliases", []),
            )
            object_names = await self._load_object_names(session, tenant_id, scenario.id)
            await session.commit()
            return self._relation_to_dict(obj, object_names)

    async def update_relation(self, relation_id: str, tenant_id: str, data: dict) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = TemplateRelationRepository(session)
            obj = await repo.get_required(relation_id, tenant_id)
            scenario = await TemplateScenarioRepository(session).get_required(obj.scenario_id, tenant_id)
            source_id = data.get("source_object_id", obj.source_object_id)
            target_id = data.get("target_object_id", obj.target_object_id)
            await self._validate_relation_objects(session, tenant_id, scenario.id, source_id, target_id)
            old_name = obj.name
            obj = await repo.update(obj, tenant_id, **{
                k: v for k, v in data.items()
                if k in (
                    "name",
                    "description",
                    "source_object_id",
                    "target_object_id",
                    "relation_type",
                    "status",
                    "ontology_code",
                    "aliases",
                ) and v is not None
            })

            new_name = data.get("name")
            if new_name and new_name != old_name:
                await self._sync_constraint_labels_by_target(
                    session, tenant_id, "relation", relation_id, new_name,
                )
            object_names = await self._load_object_names(session, tenant_id, scenario.id)
            await session.commit()
            return self._relation_to_dict(obj, object_names)

    async def delete_relation(self, relation_id: str, tenant_id: str) -> bool:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = TemplateRelationRepository(session)
            obj = await repo.get_required(relation_id, tenant_id)
            constraint_repo = TemplateConstraintRepository(session)
            constraints = await constraint_repo.list_all(
                tenant_id, 0, 10000,
                extra_conditions=[
                    TemplateConstraint.scenario_id == obj.scenario_id,
                    TemplateConstraint.target_type == "relation",
                    TemplateConstraint.target_id == relation_id,
                ],
            )
            for constraint in constraints:
                await constraint_repo.delete_soft(constraint, tenant_id)
            await repo.delete_soft(obj, tenant_id)
            await session.commit()
            return True

    async def _load_attributes(self, session, tenant_id: str, object_ids: list[str]) -> dict[str, list[TemplateAttribute]]:
        if not object_ids:
            return {}
        result = await session.execute(
            select(TemplateAttribute)
            .where(
                TemplateAttribute.tenant_id == tenant_id,
                TemplateAttribute.is_deleted == 0,
                TemplateAttribute.template_object_id.in_(object_ids),
            )
            .order_by(TemplateAttribute.sort_order.asc(), TemplateAttribute.created_at.asc())
        )
        attrs_by_object: dict[str, list[TemplateAttribute]] = {object_id: [] for object_id in object_ids}
        for attr in result.scalars():
            attrs_by_object.setdefault(attr.template_object_id, []).append(attr)
        return attrs_by_object

    async def _replace_attributes(
        self,
        session,
        tenant_id: str,
        object_id: str,
        attributes: list[dict[str, Any]],
    ) -> list[TemplateAttribute]:

        repo = TemplateAttributeRepository(session)
        constraint_repo = TemplateConstraintRepository(session)
        old_attrs = await repo.list_all(
            tenant_id,
            0,
            10000,
            extra_conditions=[TemplateAttribute.template_object_id == object_id],
        )
        old_by_id = {a.id: a for a in old_attrs}

        incoming_ids = {
            attr_data.get("id") for attr_data in attributes
            if attr_data.get("id")
        }

        removed_ids = set(old_by_id.keys()) - incoming_ids
        if removed_ids:
            removed_attrs = [old_by_id[aid] for aid in removed_ids]
            removed_attr_constraints = await constraint_repo.list_all(
                tenant_id, 0, 10000,
                extra_conditions=[
                    TemplateConstraint.target_type == "attribute",
                    TemplateConstraint.target_id.in_(list(removed_ids)),
                ],
            )
            for constraint in removed_attr_constraints:
                await constraint_repo.delete_soft(constraint, tenant_id)
            for attr in removed_attrs:
                await repo.delete_soft(attr, tenant_id)

        result: list[TemplateAttribute] = []
        for index, attr_data in enumerate(attributes):
            attr_name = attr_data.get("attr_name") or attr_data.get("name")
            if not attr_name:
                raise InvalidParameterError(message="Object attribute name must not be empty")
            attr_id = attr_data.get("id")
            if attr_id and attr_id in old_by_id:

                old_attr = old_by_id[attr_id]
                old_name = old_attr.attr_name
                updated = await repo.update(old_attr, tenant_id, **{
                    k: v for k, v in {
                        "attr_name": attr_name,
                        "description": attr_data.get("description") or attr_data.get("desc"),
                        "attr_type": attr_data.get("attr_type") or attr_data.get("type") or "string",
                        "is_primary_key": 1 if attr_data.get("is_primary_key") or attr_data.get("isPrimary") else 0,
                        "constraints_json": attr_data.get("constraints_json", {}),
                        "sort_order": attr_data.get("sort_order", index),
                        "ontology_code": attr_data.get("ontology_code"),
                        "is_required": 1 if attr_data.get("is_required") else 0,
                    }.items() if v is not None
                })

                if attr_name != old_name:
                    await self._sync_constraint_labels_by_target(
                        session, tenant_id, "attribute", attr_id, attr_name,
                    )
                result.append(updated)
            else:

                attr = await repo.create(
                    id=uuid.uuid4().hex,
                    tenant_id=tenant_id,
                    template_object_id=object_id,
                    attr_name=attr_name,
                    description=attr_data.get("description") or attr_data.get("desc"),
                    attr_type=attr_data.get("attr_type") or attr_data.get("type") or "string",
                    is_primary_key=1 if attr_data.get("is_primary_key") or attr_data.get("isPrimary") else 0,
                    constraints_json=attr_data.get("constraints_json", {}),
                    sort_order=attr_data.get("sort_order", index),
                    ontology_code=attr_data.get("ontology_code"),
                    is_required=1 if attr_data.get("is_required") else 0,
                )
                result.append(attr)
        return result

    async def _load_object_names(self, session, tenant_id: str, scenario_id: str) -> dict[str, str]:
        result = await session.execute(
            select(TemplateObject)
            .where(
                TemplateObject.tenant_id == tenant_id,
                TemplateObject.is_deleted == 0,
                TemplateObject.scenario_id == scenario_id,
            )
        )
        return {obj.id: obj.name for obj in result.scalars()}

    async def _validate_relation_objects(
        self,
        session,
        tenant_id: str,
        scenario_id: str,
        source_object_id: str | None,
        target_object_id: str | None,
    ) -> None:
        if not source_object_id or not target_object_id:
            raise InvalidParameterError(message="A relation must specify source and target objects")
        objects = await TemplateObjectRepository(session).list_all(
            tenant_id,
            0,
            2,
            extra_conditions=[
                TemplateObject.scenario_id == scenario_id,
                TemplateObject.id.in_([source_object_id, target_object_id]),
            ],
        )
        found_ids = {obj.id for obj in objects}
        if source_object_id not in found_ids or target_object_id not in found_ids:
            raise InvalidParameterError(message="Relation objects must belong to the current template scenario")

    @staticmethod
    def _object_to_dict(obj: TemplateObject, attributes: list[TemplateAttribute]) -> dict:
        data = obj.to_dict()
        data["attributes"] = [attr.to_dict() for attr in attributes]
        return data

    @staticmethod
    def _relation_to_dict(obj: TemplateRelation, object_names: dict[str, str]) -> dict:
        data = obj.to_dict()
        data["source_object_name"] = object_names.get(obj.source_object_id)
        data["target_object_name"] = object_names.get(obj.target_object_id)
        return data



    async def list_constraints(
        self, tenant_id: str, scenario_id: str, offset: int = 0, limit: int = 20,
    ) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            await TemplateScenarioRepository(session).get_required(scenario_id, tenant_id)
            repo = TemplateConstraintRepository(session)
            items = await repo.list_all(
                tenant_id, offset, limit,
                extra_conditions=[TemplateConstraint.scenario_id == scenario_id],
            )
            total = await repo.count(
                tenant_id,
                extra_conditions=[TemplateConstraint.scenario_id == scenario_id],
            )
            return {
                "items": [o.to_dict() for o in items],
                "total": total, "offset": offset, "limit": limit,
            }

    async def create_constraint(
        self, tenant_id: str, scenario_id: str, data: dict,
    ) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            scenario = await TemplateScenarioRepository(session).get_required(scenario_id, tenant_id)
            target_type = data["target_type"]
            target_id = data["target_id"]
            constraint_type = data["constraint_type"]

            if constraint_type in ("conditional", "range") and not data.get("expression"):
                raise InvalidParameterError(
                    message=f"Constraint type {constraint_type} requires an expression",
                )
            target_label = await self._validate_constraint_target(
                session, tenant_id, scenario.id, target_type, target_id,
            )
            obj = await TemplateConstraintRepository(session).create(
                id=uuid.uuid4().hex,
                tenant_id=tenant_id,
                domain_id=scenario.domain_id,
                scenario_id=scenario.id,
                name=data["name"],
                target_type=target_type,
                target_id=target_id,
                target_label=target_label,
                constraint_type=constraint_type,
                expression=data.get("expression"),
                suggestion=data.get("suggestion"),
            )
            await session.commit()
            return obj.to_dict()

    async def update_constraint(
        self, constraint_id: str, tenant_id: str, data: dict,
    ) -> dict:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = TemplateConstraintRepository(session)
            obj = await repo.get_required(constraint_id, tenant_id)
            await TemplateScenarioRepository(session).get_required(obj.scenario_id, tenant_id)


            merged_target_type = data.get("target_type", obj.target_type)
            merged_target_id = data.get("target_id", obj.target_id)
            merged_constraint_type = data.get("constraint_type", obj.constraint_type)
            merged_expression = data.get("expression", obj.expression) if "expression" in data else obj.expression


            if merged_constraint_type in ("conditional", "range") and not merged_expression:
                raise InvalidParameterError(
                    message=f"Constraint type {merged_constraint_type} requires an expression",
                )


            target_changed = (
                merged_target_type != obj.target_type
                or merged_target_id != obj.target_id
            )
            target_label = obj.target_label
            if target_changed:
                target_label = await self._validate_constraint_target(
                    session, tenant_id, obj.scenario_id,
                    merged_target_type, merged_target_id,
                )

            update_values = {
                k: v for k, v in {
                    "name": data.get("name"),
                    "target_type": data.get("target_type"),
                    "target_id": data.get("target_id"),
                    "target_label": target_label if target_changed else None,
                    "constraint_type": data.get("constraint_type"),
                    "expression": data.get("expression"),
                    "suggestion": data.get("suggestion"),
                }.items() if v is not None
            }
            obj = await repo.update(obj, tenant_id, **update_values)
            await session.commit()
            return obj.to_dict()

    async def delete_constraint(self, constraint_id: str, tenant_id: str) -> bool:
        tenant_id = _check_tenant(tenant_id)
        async with get_db_session() as session:
            repo = TemplateConstraintRepository(session)
            deleted = await repo.delete_soft(constraint_id, tenant_id)
            if not deleted:
                raise ResourceNotFoundError(message=f"Template constraint not found: {constraint_id}")
            await session.commit()
            return True

    async def _validate_constraint_target(
        self, session, tenant_id: str, scenario_id: str,
        target_type: str, target_id: str,
    ) -> str:

        valid_types = {"object", "attribute", "relation"}
        if target_type not in valid_types:
            raise InvalidParameterError(
                message=f"Invalid constraint target type: {target_type}. Valid values: {', '.join(sorted(valid_types))}",
            )
        if target_type == "object":
            objects = await TemplateObjectRepository(session).list_all(
                tenant_id, 0, 1,
                extra_conditions=[
                    TemplateObject.scenario_id == scenario_id,
                    TemplateObject.id == target_id,
                ],
            )
            if not objects:
                raise InvalidParameterError(message="Constraint target object does not belong to the current template scenario")
            return objects[0].name
        if target_type == "relation":
            relations = await TemplateRelationRepository(session).list_all(
                tenant_id, 0, 1,
                extra_conditions=[
                    TemplateRelation.scenario_id == scenario_id,
                    TemplateRelation.id == target_id,
                ],
            )
            if not relations:
                raise InvalidParameterError(message="Constraint target relation does not belong to the current template scenario")
            return relations[0].name

        if target_type == "attribute":
            result = await session.execute(
                select(TemplateAttribute, TemplateObject)
                .join(TemplateObject, TemplateAttribute.template_object_id == TemplateObject.id)
                .where(
                    TemplateAttribute.tenant_id == tenant_id,
                    TemplateAttribute.is_deleted == 0,
                    TemplateAttribute.id == target_id,
                    TemplateObject.tenant_id == tenant_id,
                    TemplateObject.is_deleted == 0,
                    TemplateObject.scenario_id == scenario_id,
                )
                .limit(1)
            )
            row = result.first()
            if not row:
                raise InvalidParameterError(
                    message="Constraint target attribute does not exist, or its owning object does not belong to the current template scenario",
                )
            return row[0].attr_name
        return ""

    async def _sync_constraint_labels_by_target(
        self, session, tenant_id: str,
        target_type: str, target_id: str, new_label: str,
    ) -> None:

        constraints = await TemplateConstraintRepository(session).list_all(
            tenant_id, 0, 10000,
            extra_conditions=[
                TemplateConstraint.target_type == target_type,
                TemplateConstraint.target_id == target_id,
            ],
        )
        for constraint in constraints:
            await TemplateConstraintRepository(session).update(
                constraint, tenant_id, target_label=new_label,
            )
