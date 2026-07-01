from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class RoomState(str, Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"


class GameState(str, Enum):
    ACTIVE = "active"
    FINISHED = "finished"


class TileState(str, Enum):
    CORRECT = "correct"    
    PRESENT = "present"    
    ABSENT = "absent"      
    EMPTY = "empty"        


@dataclass
class TileResult:
    letter: str
    state: TileState

    def to_dict(self) -> dict:
        return {"letter": self.letter, "state": self.state.value}


@dataclass
class GuessRecord:
    word: str
    tiles: List[TileResult]
    submitted_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "word": self.word,
            "tiles": [t.to_dict() for t in self.tiles],
            "submitted_at": self.submitted_at.isoformat(),
        }


@dataclass
class PlayerGameState:
    player_id: str
    guesses: List[GuessRecord] = field(default_factory=list)
    won: bool = False
    finished: bool = False
    finish_time: Optional[datetime] = None
    rank: Optional[int] = None

    @property
    def attempts_used(self) -> int:
        return len(self.guesses)

    def to_dict(self) -> dict:
        return {
            "player_id": self.player_id,
            "guesses": [g.to_dict() for g in self.guesses],
            "attempts_used": self.attempts_used,
            "won": self.won,
            "finished": self.finished,
            "finish_time": self.finish_time.isoformat() if self.finish_time else None,
            "rank": self.rank,
        }

    def to_public_dict(self) -> dict:
        
        return {
            "player_id": self.player_id,
            "attempts_used": self.attempts_used,
            "won": self.won,
            "finished": self.finished,
            "rank": self.rank,
            "tiles_history": [
                [t.state.value for t in g.tiles] for g in self.guesses
            ],
        }


@dataclass
class Game:
    id: str
    room_id: str
    word: str
    word_length: int
    max_attempts: int
    player_states: Dict[str, PlayerGameState] = field(default_factory=dict)
    state: GameState = GameState.ACTIVE
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    winner_id: Optional[str] = None

    def get_rankings(self) -> List[dict]:
        finishers = [
            s for s in self.player_states.values() if s.finished and s.won
        ]
        non_finishers = [
            s for s in self.player_states.values() if s.finished and not s.won
        ]
        still_playing = [
            s for s in self.player_states.values() if not s.finished
        ]

        finishers.sort(key=lambda s: (s.attempts_used, s.finish_time or datetime.utcnow()))
        non_finishers.sort(key=lambda s: -s.attempts_used)

        rankings = []
        rank = 1
        for state in finishers:
            state.rank = rank
            rankings.append(state)
            rank += 1
        for state in non_finishers + still_playing:
            state.rank = rank
            rankings.append(state)
            rank += 1

        return rankings

    def to_dict(self, reveal_word: bool = False) -> dict:
        return {
            "id": self.id,
            "room_id": self.room_id,
            "word": self.word if reveal_word else None,
            "word_length": self.word_length,
            "max_attempts": self.max_attempts,
            "state": self.state.value,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "winner_id": self.winner_id,
            "player_states": {
                pid: state.to_public_dict()
                for pid, state in self.player_states.items()
            },
        }


@dataclass
class RoomSettings:
    word_length: int = 5
    max_attempts: int = 6

    def to_dict(self) -> dict:
        return {
            "word_length": self.word_length,
            "max_attempts": self.max_attempts,
        }


@dataclass
class Player:
    id: str
    nickname: str
    socket_id: str
    room_id: Optional[str] = None
    connected: bool = True
    disconnected_at: Optional[datetime] = None
    last_seen: datetime = field(default_factory=datetime.utcnow)
    is_host: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nickname": self.nickname,
            "is_host": self.is_host,
            "connected": self.connected,
        }


@dataclass
class Room:
    id: str
    code: str
    host_id: str
    players: Dict[str, Player] = field(default_factory=dict)
    settings: RoomSettings = field(default_factory=RoomSettings)
    state: RoomState = RoomState.WAITING
    game: Optional[Game] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)

    @property
    def connected_players(self) -> List[Player]:
        return [p for p in self.players.values() if p.connected]

    @property
    def player_count(self) -> int:
        return len(self.connected_players)

    def touch(self) -> None:
        self.last_activity = datetime.utcnow()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "code": self.code,
            "host_id": self.host_id,
            "state": self.state.value,
            "settings": self.settings.to_dict(),
            "players": [p.to_dict() for p in self.players.values()],
            "player_count": self.player_count,
        }
