"""CRUD operations for Template model."""

from typing import Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.template import Template


class TemplateCRUD:
    """CRUD operations for Template model."""

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        template_id: str,
        include_services: bool = False,
    ) -> Template | None:
        """Get a template by ID."""
        query = select(Template).where(Template.id == template_id)

        if include_services:
            query = query.options(selectinload(Template.services))

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_slug(db: AsyncSession, slug: str) -> Template | None:
        """Get a template by slug."""
        query = select(Template).where(Template.slug == slug)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        workload_type: str | None = None,
        language: str | None = None,
        is_active: bool | None = True,
        is_recommended: bool | None = None,
    ) -> Sequence[Template]:
        """Get all templates with optional filtering."""
        query = select(Template)

        if workload_type:
            query = query.where(Template.workload_type == workload_type)
        if language:
            query = query.where(Template.language == language)
        if is_active is not None:
            query = query.where(Template.is_active == is_active)
        if is_recommended is not None:
            query = query.where(Template.is_recommended == is_recommended)

        query = query.offset(skip).limit(limit).order_by(Template.name)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def count(
        db: AsyncSession,
        workload_type: str | None = None,
        language: str | None = None,
        is_active: bool | None = True,
    ) -> int:
        """Count templates with optional filtering."""
        query = select(func.count(Template.id))

        if workload_type:
            query = query.where(Template.workload_type == workload_type)
        if language:
            query = query.where(Template.language == language)
        if is_active is not None:
            query = query.where(Template.is_active == is_active)

        result = await db.execute(query)
        return result.scalar_one()

    @staticmethod
    async def exists(db: AsyncSession, template_id: str) -> bool:
        """Check if a template exists."""
        result = await db.execute(
            select(func.count(Template.id)).where(Template.id == template_id)
        )
        return result.scalar_one() > 0

    @staticmethod
    async def increment_usage(db: AsyncSession, template: Template) -> Template:
        """Increment the usage count of a template."""
        template.usage_count += 1
        await db.commit()
        await db.refresh(template)
        return template
