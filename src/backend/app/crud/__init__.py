"""CRUD operations for database models."""

from app.crud.service import ServiceCRUD
from app.crud.team import TeamCRUD
from app.crud.template import TemplateCRUD

__all__ = ["ServiceCRUD", "TeamCRUD", "TemplateCRUD"]
