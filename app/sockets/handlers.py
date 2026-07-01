
from __future__ import annotations
import logging
from typing import Any

from flask import request
from flask_socketio import SocketIO, emit, join_room as sio_join_room, leave_room as sio_leave_room

from app.domain.exceptions import WordleRaceError
from app.services.game_service import GameService
from app.services.room_service import RoomService
from app.sockets import events as ev

logger = logging.getLogger(__name__)




_sio: SocketIO | None = None


def _err(code: str, message: str) -> None:
    
    emit(ev.ERROR, {"code": code, "message": message})


def _broadcast(event: str, data: dict, room_id: str, skip_sid: str | None = None) -> None:
    
    _sio.emit(event, data, to=room_id, namespace="/", skip_sid=skip_sid)


def _resolve_player(room_svc: RoomService, sid: str, player_id: str | None = None):
    
    player = room_svc.get_player_by_socket(sid)
    if player:
        return player
    if player_id:
        player = room_svc.get_player_by_id(player_id)
        if player:
            room_svc.update_player_socket(player.id, sid)
            logger.debug("Resolved player %s via player_id (socket re-associated)", player.nickname)
    return player


def register_handlers(socketio: SocketIO, room_svc: RoomService, game_svc: GameService) -> None:
    global _sio
    _sio = socketio

    
    
    

    @socketio.on("connect")
    def on_connect():
        logger.debug("Socket connected: %s", request.sid)

    @socketio.on("disconnect")
    def on_disconnect():
        sid = request.sid
        logger.debug("Socket disconnected: %s", sid)

        player, room, new_host_id = room_svc.handle_disconnect(sid)
        if not player or not room:
            return

        _broadcast(
            ev.PLAYER_DISCONNECTED,
            {"player_id": player.id, "nickname": player.nickname},
            room.id,
            skip_sid=sid,
        )

        if new_host_id:
            host = room.players.get(new_host_id)
            _broadcast(
                ev.HOST_CHANGED,
                {
                    "new_host_id": new_host_id,
                    "new_host_nickname": host.nickname if host else "",
                },
                room.id,
            )

    
    
    

    @socketio.on(ev.CREATE_ROOM)
    def on_create_room(data: dict[str, Any]):
        try:
            nickname = str(data.get("nickname", "")).strip()
            settings = data.get("settings", {})
            room, player = room_svc.create_room(nickname, request.sid, settings)
            sio_join_room(room.id)
            emit(ev.ROOM_CREATED, {
                "room_code": room.code,
                "room_id": room.id,
                "player": player.to_dict(),
                "room": room.to_dict(),
            })
        except WordleRaceError as exc:
            _err(exc.code, exc.message)
        except Exception as exc:
            logger.exception("Unexpected error in create_room: %s", exc)
            _err("INTERNAL_ERROR", "Error interno del servidor.")

    @socketio.on(ev.JOIN_ROOM)
    def on_join_room(data: dict[str, Any]):
        try:
            nickname = str(data.get("nickname", "")).strip()
            room_code = str(data.get("room_code", "")).strip().upper()
            room, player = room_svc.join_room(room_code, nickname, request.sid)
            sio_join_room(room.id)

            emit(ev.ROOM_JOINED, {
                "room": room.to_dict(),
                "player": player.to_dict(),
            })

            _broadcast(
                ev.PLAYER_JOINED,
                {"player": player.to_dict()},
                room.id,
                skip_sid=request.sid,
            )
        except WordleRaceError as exc:
            _err(exc.code, exc.message)
        except Exception as exc:
            logger.exception("Unexpected error in join_room: %s", exc)
            _err("INTERNAL_ERROR", "Error interno del servidor.")

    @socketio.on(ev.LEAVE_ROOM)
    def on_leave_room():
        try:
            player = room_svc.get_player_by_socket(request.sid)
            if not player:
                return

            room, deleted, new_host_id = room_svc.leave_room(player.id)
            if not room:
                return

            sio_leave_room(room.id)

            if not deleted:
                _broadcast(
                    ev.PLAYER_LEFT,
                    {
                        "player_id": player.id,
                        "nickname": player.nickname,
                        "new_host_id": new_host_id,
                    },
                    room.id,
                )
                if new_host_id:
                    new_host = room.players.get(new_host_id)
                    _broadcast(
                        ev.HOST_CHANGED,
                        {
                            "new_host_id": new_host_id,
                            "new_host_nickname": new_host.nickname if new_host else "",
                        },
                        room.id,
                    )
        except WordleRaceError as exc:
            _err(exc.code, exc.message)
        except Exception as exc:
            logger.exception("Unexpected error in leave_room: %s", exc)
            _err("INTERNAL_ERROR", "Error interno del servidor.")

    @socketio.on(ev.RESET_ROOM)
    def on_reset_room(data: dict[str, Any] | None = None):
        data = data or {}
        try:
            player = _resolve_player(room_svc, request.sid, data.get("player_id"))
            if not player:
                _err("PLAYER_NOT_FOUND", "Jugador no encontrado.")
                return
            room = room_svc.reset_room(player.id)
            _broadcast(ev.ROOM_UPDATED, {"room": room.to_dict()}, room.id)
            emit(ev.ROOM_UPDATED, {"room": room.to_dict()})
        except WordleRaceError as exc:
            _err(exc.code, exc.message)
        except Exception as exc:
            logger.exception("Unexpected error in reset_room: %s", exc)
            _err("INTERNAL_ERROR", "Error interno del servidor.")

    @socketio.on(ev.UPDATE_SETTINGS)
    def on_update_settings(data: dict[str, Any]):
        try:
            player = _resolve_player(room_svc, request.sid, data.get("player_id"))
            if not player:
                _err("PLAYER_NOT_FOUND", "Jugador no encontrado.")
                return

            settings = data.get("settings", {})
            room = room_svc.update_settings(player.id, settings)
            _broadcast(ev.ROOM_UPDATED, {"room": room.to_dict()}, room.id)
        except WordleRaceError as exc:
            _err(exc.code, exc.message)
        except Exception as exc:
            logger.exception("Unexpected error in update_settings: %s", exc)
            _err("INTERNAL_ERROR", "Error interno del servidor.")

    
    
    

    @socketio.on(ev.START_GAME)
    def on_start_game(data: dict[str, Any] | None = None):
        data = data or {}
        try:
            player = _resolve_player(room_svc, request.sid, data.get("player_id"))
            if not player:
                logger.warning("start_game: no player for sid=%s player_id=%s", request.sid, data.get("player_id"))
                _err("PLAYER_NOT_FOUND", "Jugador no encontrado.")
                return

            room, game = game_svc.start_game(player.id)
            payload = {
                "word_length": game.word_length,
                "max_attempts": game.max_attempts,
                "player_ids": list(game.player_states.keys()),
            }
            logger.info("game_started → room %s (word=%s)", room.id, game.word)
            
            emit(ev.GAME_STARTED, payload)
            
            _broadcast(ev.GAME_STARTED, payload, room.id, skip_sid=request.sid)
        except WordleRaceError as exc:
            _err(exc.code, exc.message)
        except Exception as exc:
            logger.exception("Unexpected error in start_game: %s", exc)
            _err("INTERNAL_ERROR", "Error interno del servidor.")

    @socketio.on(ev.SUBMIT_GUESS)
    def on_submit_guess(data: dict[str, Any]):
        try:
            player = _resolve_player(room_svc, request.sid, data.get("player_id"))
            if not player:
                _err("PLAYER_NOT_FOUND", "Jugador no encontrado.")
                return

            word = str(data.get("word", "")).strip()
            result = game_svc.submit_guess(player.id, word)

            record = result["guess_record"]
            game = result["game"]
            room = result["room"]

            
            emit(ev.GUESS_RESULT, {
                "player_id": player.id,
                "word": record.word,
                "tiles": [t.to_dict() for t in record.tiles],
                "attempts_used": result["attempts_used"],
                "attempts_left": result["attempts_left"],
                "won": result["won"],
            })

            
            pstate = game.player_states[player.id]
            _broadcast(
                ev.PLAYER_PROGRESS,
                {
                    "player_id": player.id,
                    "attempts_used": result["attempts_used"],
                    "won": result["won"],
                    "finished": result["player_finished"],
                    "tiles_history": [
                        [t.state.value for t in g.tiles] for g in pstate.guesses
                    ],
                },
                room.id,
                skip_sid=request.sid,
            )

            if result["game_finished"]:
                rankings_payload = []
                for rank_state in result["rankings"]:
                    p = room.players.get(rank_state.player_id)
                    rankings_payload.append({
                        "rank": rank_state.rank,
                        "player_id": rank_state.player_id,
                        "nickname": p.nickname if p else "?",
                        "attempts_used": rank_state.attempts_used,
                        "won": rank_state.won,
                        "guesses": [g.to_dict() for g in rank_state.guesses],
                    })

                _broadcast(
                    ev.GAME_FINISHED,
                    {
                        "word": game.word,
                        "winner_id": game.winner_id,
                        "rankings": rankings_payload,
                    },
                    room.id,
                )
        except WordleRaceError as exc:
            _err(exc.code, exc.message)
        except Exception as exc:
            logger.exception("Unexpected error in submit_guess: %s", exc)
            _err("INTERNAL_ERROR", "Error interno del servidor.")

    
    
    

    @socketio.on(ev.RECONNECT_PLAYER)
    def on_reconnect(data: dict[str, Any]):
        try:
            player_id = str(data.get("player_id", "")).strip()
            room_code = str(data.get("room_code", "")).strip().upper()

            player, room = room_svc.reconnect_player(player_id, room_code, request.sid)
            sio_join_room(room.id)

            game_dict = None
            if room.game:
                game_dict = room.game.to_dict()
                pstate = room.game.player_states.get(player_id)
                if pstate:
                    game_dict["my_guesses"] = [g.to_dict() for g in pstate.guesses]

            emit(ev.RECONNECTED, {
                "player": player.to_dict(),
                "room": room.to_dict(),
                "game": game_dict,
            })

            _broadcast(
                ev.PLAYER_JOINED,
                {"player": player.to_dict()},
                room.id,
                skip_sid=request.sid,
            )
        except WordleRaceError as exc:
            _err(exc.code, exc.message)
        except Exception as exc:
            logger.exception("Unexpected error in reconnect_player: %s", exc)
            _err("INTERNAL_ERROR", "Error interno del servidor.")

    
    
    

    @socketio.on(ev.PING)
    def on_ping(data: dict[str, Any]):
        emit(ev.PONG, {"timestamp": data.get("timestamp")})
