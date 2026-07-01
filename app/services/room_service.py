from __future__ import annotations
import logging
import random
import string
import uuid
from datetime import datetime
from typing import Optional, Tuple

from app.config import Config
from app.domain.exceptions import (
    InvalidSettingsError,
    NicknameRequiredError,
    NotHostError,
    PlayerNotFoundError,
    RoomFullError,
    RoomNotFoundError,
    RoomNotInStateError,
)
from app.domain.models import Player, Room, RoomSettings, RoomState
from app.repositories.base import AbstractPlayerRepository, AbstractRoomRepository

logger = logging.getLogger(__name__)

_CODE_CHARS = string.ascii_uppercase + string.digits
_CODE_LENGTH = 6


def _generate_code() -> str:
    return "".join(random.choices(_CODE_CHARS, k=_CODE_LENGTH))


def _generate_id() -> str:
    return uuid.uuid4().hex


class RoomService:
    def __init__(
        self,
        room_repo: AbstractRoomRepository,
        player_repo: AbstractPlayerRepository,
    ):
        self._rooms = room_repo
        self._players = player_repo

    # ------------------------------------------------------------------
    # Room lifecycle
    # ------------------------------------------------------------------

    def create_room(
        self, nickname: str, socket_id: str, settings: dict
    ) -> Tuple[Room, Player]:
        nickname = self._validate_nickname(nickname)
        parsed_settings = self._parse_settings(settings)

        code = self._unique_code()
        room_id = _generate_id()
        player_id = _generate_id()

        player = Player(
            id=player_id,
            nickname=nickname,
            socket_id=socket_id,
            room_id=room_id,
            is_host=True,
        )
        room = Room(
            id=room_id,
            code=code,
            host_id=player_id,
            settings=parsed_settings,
        )
        room.players[player_id] = player

        self._rooms.create(room)
        self._players.create(player)

        logger.info("Room %s created by %s (code=%s)", room_id, nickname, code)
        return room, player

    def join_room(
        self, room_code: str, nickname: str, socket_id: str
    ) -> Tuple[Room, Player]:
        nickname = self._validate_nickname(nickname)
        room = self._rooms.get_by_code(room_code)
        if not room:
            raise RoomNotFoundError(room_code)
        if room.state != RoomState.WAITING:
            raise RoomNotInStateError("waiting", room.state.value)
        if room.player_count >= Config.MAX_PLAYERS_PER_ROOM:
            raise RoomFullError()

        player_id = _generate_id()
        player = Player(
            id=player_id,
            nickname=nickname,
            socket_id=socket_id,
            room_id=room.id,
            is_host=False,
        )
        room.players[player_id] = player
        room.touch()

        self._players.create(player)
        self._rooms.update(room)

        logger.info("Player %s joined room %s", nickname, room.code)
        return room, player

    def leave_room(
        self, player_id: str
    ) -> Tuple[Optional[Room], bool, Optional[str]]:
        """
        Returns (room_or_None, room_deleted, new_host_id_or_None).
        """
        player = self._players.get(player_id)
        if not player or not player.room_id:
            return None, False, None

        room = self._rooms.get(player.room_id)
        if not room:
            self._players.delete(player_id)
            return None, False, None

        # Remove player from room and global store
        room.players.pop(player_id, None)
        self._players.delete(player_id)

        # If room is now empty, delete it
        if not room.players:
            self._rooms.delete(room.id)
            logger.info("Room %s deleted (empty)", room.code)
            return room, True, None

        # Transfer host if necessary
        new_host_id: Optional[str] = None
        if room.host_id == player_id:
            new_host = next(iter(room.players.values()))
            new_host.is_host = True
            room.host_id = new_host.id
            new_host_id = new_host.id
            self._players.update(new_host)
            logger.info("Host transferred to %s in room %s", new_host.nickname, room.code)

        room.touch()
        self._rooms.update(room)
        return room, False, new_host_id

    def handle_disconnect(
        self, socket_id: str
    ) -> Tuple[Optional[Player], Optional[Room], Optional[str]]:
        """
        Mark player as disconnected without removing them immediately.
        Returns (player, room, new_host_id_or_None).
        """
        player = self._players.get_by_socket(socket_id)
        if not player:
            return None, None, None

        player.connected = False
        player.disconnected_at = datetime.utcnow()
        self._players.update(player)

        room = self._rooms.get(player.room_id) if player.room_id else None
        new_host_id: Optional[str] = None

        if room:
            # If disconnected player was host, transfer immediately
            if room.host_id == player.id:
                connected = [p for p in room.players.values() if p.connected and p.id != player.id]
                if connected:
                    new_host = connected[0]
                    new_host.is_host = True
                    room.host_id = new_host.id
                    new_host_id = new_host.id
                    self._players.update(new_host)
            room.touch()
            self._rooms.update(room)

        return player, room, new_host_id

    def reconnect_player(
        self, player_id: str, room_code: str, new_socket_id: str
    ) -> Tuple[Player, Room]:
        player = self._players.get(player_id)
        if not player:
            raise PlayerNotFoundError(player_id)

        room = self._rooms.get_by_code(room_code)
        if not room or room.id != player.room_id:
            raise RoomNotFoundError(room_code)

        player.socket_id = new_socket_id
        player.connected = True
        player.disconnected_at = None
        player.last_seen = datetime.utcnow()
        self._players.update(player)
        room.touch()
        self._rooms.update(room)

        logger.info("Player %s reconnected to room %s", player.nickname, room.code)
        return player, room

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def update_settings(self, player_id: str, settings: dict) -> Room:
        player = self._players.get(player_id)
        if not player:
            raise PlayerNotFoundError(player_id)

        room = self._rooms.get(player.room_id)
        if not room:
            raise RoomNotFoundError(player.room_id or "")
        if room.host_id != player_id:
            raise NotHostError()
        if room.state != RoomState.WAITING:
            raise RoomNotInStateError("waiting", room.state.value)

        room.settings = self._parse_settings(settings)
        room.touch()
        self._rooms.update(room)
        return room

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_room_by_player(self, player_id: str) -> Optional[Room]:
        player = self._players.get(player_id)
        if not player or not player.room_id:
            return None
        return self._rooms.get(player.room_id)

    def get_player_by_socket(self, socket_id: str) -> Optional[Player]:
        return self._players.get_by_socket(socket_id)

    def get_player_by_id(self, player_id: str) -> Optional[Player]:
        return self._players.get(player_id)

    def reset_room(self, player_id: str) -> Room:
        """Reset a finished room back to WAITING so the host can start a new game."""
        player = self._players.get(player_id)
        if not player:
            raise PlayerNotFoundError(player_id)
        room = self._rooms.get(player.room_id)
        if not room:
            raise RoomNotFoundError(player.room_id or "")
        if room.host_id != player_id:
            raise NotHostError()
        room.state = RoomState.WAITING
        room.game = None
        room.touch()
        self._rooms.update(room)
        return room

    def update_player_socket(self, player_id: str, new_socket_id: str) -> None:
        """Re-associate a player with a new socket without full reconnect flow."""
        player = self._players.get(player_id)
        if player and player.socket_id != new_socket_id:
            player.socket_id = new_socket_id
            player.connected = True
            player.disconnected_at = None
            self._players.update(player)
            logger.debug("Player %s socket updated to %s", player.nickname, new_socket_id)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def cleanup_expired_rooms(self) -> int:
        now = datetime.utcnow()
        expired = [
            r for r in self._rooms.list_all()
            if (now - r.last_activity).total_seconds() > Config.ROOM_EXPIRY_SECONDS
        ]
        for room in expired:
            for pid in list(room.players.keys()):
                self._players.delete(pid)
            self._rooms.delete(room.id)
            logger.info("Expired room %s removed", room.code)
        return len(expired)

    def cleanup_ghost_players(self) -> int:
        """Remove disconnected players who exceeded the reconnection window."""
        now = datetime.utcnow()
        removed = 0
        for room in self._rooms.list_all():
            ghosts = [
                p for p in room.players.values()
                if not p.connected
                and p.disconnected_at
                and (now - p.disconnected_at).total_seconds() > Config.RECONNECT_WINDOW_SECONDS
            ]
            for ghost in ghosts:
                room.players.pop(ghost.id, None)
                self._players.delete(ghost.id)
                removed += 1
            if ghosts:
                if not room.players:
                    self._rooms.delete(room.id)
                else:
                    self._rooms.update(room)
        return removed

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _unique_code(self) -> str:
        for _ in range(10):
            code = _generate_code()
            if not self._rooms.get_by_code(code):
                return code
        raise RuntimeError("Could not generate a unique room code after 10 tries.")

    @staticmethod
    def _validate_nickname(nickname: str) -> str:
        cleaned = nickname.strip()[:20]
        if not cleaned:
            raise NicknameRequiredError()
        return cleaned

    @staticmethod
    def _parse_settings(data: dict) -> RoomSettings:
        return RoomSettings(word_length=5, max_attempts=6)
