#!/usr/bin/python3



from jonex_core.common.repository import BaseRepository

from ..models.space import Space, SpacePermission


class SpaceRepository(BaseRepository[Space]):
    model = Space


class SpacePermissionRepository(BaseRepository[SpacePermission]):
    model = SpacePermission
