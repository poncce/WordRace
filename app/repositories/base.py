
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from app.domain.models import Player, Room


class AbstractRoomRepository(ABC):
    @abstractmethod
    def create(self, room: Room) -> Room: ...

    @abstractmethod
    def get(self, room_id: str) -> Optional[Room]: ...

    @abstractmethod
    def get_by_code(self, code: str) -> Optional[Room]: ...

    @abstractmethod
    def update(self, room: Room) -> Room: ...

    @abstractmethod
    def delete(self, room_id: str) -> bool: ...

    @abstractmethod
    def list_all(self) -> List[Room]: ...


class AbstractPlayerRepository(ABC):
    @abstractmethod
    def create(self, player: Player) -> Player: ...

    @abstractmethod
    def get(self, player_id: str) -> Optional[Player]: ...

    @abstractmethod
    def get_by_socket(self, socket_id: str) -> Optional[Player]: ...

    @abstractmethod
    def update(self, player: Player) -> Player: ...

    @abstractmethod
    def delete(self, player_id: str) -> bool: ...

    @abstractmethod
    def list_by_room(self, room_id: str) -> List[Player]: ...


class AbstractWordCacheRepository(ABC):
    @abstractmethod
    def get(self, word: str) -> Optional[bool]: ...

    @abstractmethod
    def set(self, word: str, valid: bool) -> None: ...

    @abstractmethod
    def size(self) -> int: ...
