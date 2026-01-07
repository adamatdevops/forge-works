"""CRUD operations for Team model."""

from typing import Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.team import Team


class TeamCRUD:
    """CRUD operations for Team model."""

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        team_id: str,
        include_services: bool = False,
    ) -> Team | None:
        """Get a team by ID."""
        query = select(Team).where(Team.id == team_id)

        if include_services:
            query = query.options(selectinload(Team.services))

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_slug(db: AsyncSession, slug: str) -> Team | None:
        """Get a team by slug."""
        query = select(Team).where(Team.slug == slug)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[Team]:
        """Get all teams."""
        query = select(Team).offset(skip).limit(limit).order_by(Team.name)
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def count(db: AsyncSession) -> int:
        """Count all teams."""
        result = await db.execute(select(func.count(Team.id)))
        return result.scalar_one()

    @staticmethod
    async def exists(db: AsyncSession, team_id: str) -> bool:
        """Check if a team exists."""
        result = await db.execute(
            select(func.count(Team.id)).where(Team.id == team_id)
        )
        return result.scalar_one() > 0
