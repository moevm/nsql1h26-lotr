from __future__ import annotations

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    '''
    Custom User model.

    Expands on AbstractUser by adding 'role' field.
    Role is stored in SQLite DB (not in Neo4J) - JWT
    checks role in every request (or else there would be
    an extra RTT to Neo4j). Role is encoded in JWT as
    custom claim.
    '''

    class Role(models.TextChoices):
        VIEWER = 'viewer', 'Viewer'
        ADMIN = 'admin', 'Admin'

    role: models.CharField[str, str] = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.VIEWER
    )

    class Meta:
        db_table = 'users'

    def __str__(self) -> str:
        return f'{self.username} ({self.role})'

    @property
    def is_admin(self) -> bool:
        return self.role == self.Role.ADMIN

    @property
    def is_viewer(self) -> bool:
        return self.role == self.Role.VIEWER
