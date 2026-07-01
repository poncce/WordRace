"""
In-memory implementations of all repository interfaces.

All data lives in Python dicts protected by RLock for thread safety.
To migrate to Redis or a DB, implement the ABC interfaces in a new module.
"""
from __future__ import annotations
import threading
from typing import Dict, List, Optional

from app.domain.models import Player, Room
from app.repositories.base import (
    AbstractPlayerRepository,
    AbstractRoomRepository,
    AbstractWordCacheRepository,
)


class MemoryRoomRepository(AbstractRoomRepository):
    def __init__(self):
        self._rooms: Dict[str, Room] = {}
        self._code_index: Dict[str, str] = {}  # code -> room_id
        self._lock = threading.RLock()

    def create(self, room: Room) -> Room:
        with self._lock:
            self._rooms[room.id] = room
            self._code_index[room.code] = room.id
            return room

    def get(self, room_id: str) -> Optional[Room]:
        with self._lock:
            return self._rooms.get(room_id)

    def get_by_code(self, code: str) -> Optional[Room]:
        with self._lock:
            room_id = self._code_index.get(code.upper())
            if not room_id:
                return None
            return self._rooms.get(room_id)

    def update(self, room: Room) -> Room:
        with self._lock:
            self._rooms[room.id] = room
            return room

    def delete(self, room_id: str) -> bool:
        with self._lock:
            room = self._rooms.pop(room_id, None)
            if room:
                self._code_index.pop(room.code, None)
                return True
            return False

    def list_all(self) -> List[Room]:
        with self._lock:
            return list(self._rooms.values())


class MemoryPlayerRepository(AbstractPlayerRepository):
    def __init__(self):
        self._players: Dict[str, Player] = {}
        self._socket_index: Dict[str, str] = {}  # socket_id -> player_id
        self._lock = threading.RLock()

    def create(self, player: Player) -> Player:
        with self._lock:
            self._players[player.id] = player
            self._socket_index[player.socket_id] = player.id
            return player

    def get(self, player_id: str) -> Optional[Player]:
        with self._lock:
            return self._players.get(player_id)

    def get_by_socket(self, socket_id: str) -> Optional[Player]:
        with self._lock:
            player_id = self._socket_index.get(socket_id)
            if not player_id:
                return None
            return self._players.get(player_id)

    def update(self, player: Player) -> Player:
        with self._lock:
            old = self._players.get(player.id)
            if old and old.socket_id != player.socket_id:
                self._socket_index.pop(old.socket_id, None)
                self._socket_index[player.socket_id] = player.id
            self._players[player.id] = player
            return player

    def delete(self, player_id: str) -> bool:
        with self._lock:
            player = self._players.pop(player_id, None)
            if player:
                self._socket_index.pop(player.socket_id, None)
                return True
            return False

    def list_by_room(self, room_id: str) -> List[Player]:
        with self._lock:
            return [p for p in self._players.values() if p.room_id == room_id]


class MemoryWordCacheRepository(AbstractWordCacheRepository):
    def __init__(self):
        self._cache: Dict[str, bool] = {}
        self._lock = threading.RLock()

    def get(self, word: str) -> Optional[bool]:
        with self._lock:
            return self._cache.get(word)

    def set(self, word: str, valid: bool) -> None:
        with self._lock:
            self._cache[word] = valid

    def size(self) -> int:
        with self._lock:
            return len(self._cache)
