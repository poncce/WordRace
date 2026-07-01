from __future__ import annotations
import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from app.config import Config
from app.domain.exceptions import (
    AlreadyFinishedError,
    GameNotActiveError,
    NotHostError,
    PlayerNotFoundError,
    RateLimitError,
    RoomNotFoundError,
    RoomNotInStateError,
)
from app.domain.models import Game, GameState, PlayerGameState, Room, RoomState
from app.repositories.base import AbstractPlayerRepository, AbstractRoomRepository

if TYPE_CHECKING:
    from app.services.word_service import WordValidationService

logger = logging.getLogger(__name__)


class GameService:
    def __init__(
        self,
        room_repo: AbstractRoomRepository,
        player_repo: AbstractPlayerRepository,
        word_service: "WordValidationService",
    ):
        self._rooms = room_repo
        self._players = player_repo
        self._word_service = word_service
        # rate-limit tracker: player_id -> list of timestamps
        self._guess_times: dict[str, list[datetime]] = {}

    # ------------------------------------------------------------------
    # Game lifecycle
    # ------------------------------------------------------------------

    def start_game(self, player_id: str) -> tuple[Room, Game]:
        player = self._players.get(player_id)
        if not player:
            raise PlayerNotFoundError(player_id)

        room = self._rooms.get(player.room_id)
        if not room:
            raise RoomNotFoundError(player.room_id or "")
        if room.host_id != player_id:
            raise NotHostError()
        if room.state not in (RoomState.WAITING, RoomState.FINISHED):
            raise RoomNotInStateError("waiting", room.state.value)
        if room.player_count < 1:
            raise RoomNotInStateError("waiting", "sin jugadores")

        # Reset from a previous finished game
        if room.state == RoomState.FINISHED:
            room.state = RoomState.WAITING
            room.game = None
            self._rooms.update(room)

        word = self._word_service.get_random_word(room.settings.word_length)
        game_id = uuid.uuid4().hex

        player_states = {
            pid: PlayerGameState(player_id=pid)
            for pid in room.players
        }

        game = Game(
            id=game_id,
            room_id=room.id,
            word=word,
            word_length=room.settings.word_length,
            max_attempts=room.settings.max_attempts,
            player_states=player_states,
        )

        room.game = game
        room.state = RoomState.PLAYING
        room.touch()
        self._rooms.update(room)

        logger.info(
            "Game %s started in room %s (word=%s, length=%d, attempts=%d)",
            game_id, room.code, word, room.settings.word_length, room.settings.max_attempts,
        )
        return room, game

    def submit_guess(
        self, player_id: str, raw_word: str
    ) -> dict:
        """
        Process a player's guess.

        Returns a result dict with:
          - guess_record: GuessRecord
          - won: bool
          - attempts_used: int
          - attempts_left: int
          - player_finished: bool
          - game_finished: bool
          - game: Game
          - room: Room
          - rankings: list (populated when game finishes)
        """
        player = self._players.get(player_id)
        if not player:
            raise PlayerNotFoundError(player_id)

        room = self._rooms.get(player.room_id)
        if not room or not room.game:
            raise GameNotActiveError()
        if room.state != RoomState.PLAYING:
            raise GameNotActiveError()

        game = room.game
        if game.state != GameState.ACTIVE:
            raise GameNotActiveError()

        pstate = game.player_states.get(player_id)
        if not pstate:
            raise PlayerNotFoundError(player_id)
        if pstate.finished:
            raise AlreadyFinishedError()

        self._enforce_rate_limit(player_id)

        # Validate word + evaluate (raises on invalid word)
        record = self._word_service.validate_and_evaluate(
            raw_word, game.word, game.word_length
        )

        pstate.guesses.append(record)

        won = all(t.state.value == "correct" for t in record.tiles)
        attempts_used = pstate.attempts_used
        attempts_left = game.max_attempts - attempts_used

        if won or attempts_left <= 0:
            pstate.won = won
            pstate.finished = True
            pstate.finish_time = datetime.utcnow()

        # Check whether the entire game is over
        game_finished = self._is_game_finished(game)
        rankings: list = []

        if game_finished:
            game.state = GameState.FINISHED
            game.finished_at = datetime.utcnow()
            if won and not game.winner_id:
                game.winner_id = player_id
            rankings = game.get_rankings()
            room.state = RoomState.FINISHED

        room.touch()
        self._rooms.update(room)

        return {
            "guess_record": record,
            "won": won,
            "attempts_used": attempts_used,
            "attempts_left": attempts_left,
            "player_finished": pstate.finished,
            "game_finished": game_finished,
            "game": game,
            "room": room,
            "rankings": rankings,
        }

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_game_for_player(self, player_id: str) -> Optional[Game]:
        player = self._players.get(player_id)
        if not player or not player.room_id:
            return None
        room = self._rooms.get(player.room_id)
        return room.game if room else None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    @staticmethod
    def _is_game_finished(game: Game) -> bool:
        # Game ends when any player wins
        if any(s.won for s in game.player_states.values()):
            return True
        # Or all connected players are out of attempts
        active = [s for s in game.player_states.values() if not s.finished]
        return len(active) == 0

    def _enforce_rate_limit(self, player_id: str) -> None:
        now = datetime.utcnow()
        history = self._guess_times.setdefault(player_id, [])
        # Keep only the last 60 seconds
        history[:] = [t for t in history if (now - t).total_seconds() < 60]
        if len(history) >= Config.GUESS_RATE_LIMIT:
            raise RateLimitError()
        history.append(now)
