import logging
from flask import Blueprint, jsonify, current_app

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/health")
def health():
    return jsonify({"status": "ok"})


@api_bp.get("/stats")
def stats():
    room_svc = current_app.room_service
    rooms = room_svc._rooms.list_all()
    active_games = sum(1 for r in rooms if r.state.value == "playing")
    total_players = sum(r.player_count for r in rooms)
    return jsonify({
        "total_rooms": len(rooms),
        "active_games": active_games,
        "total_players": total_players,
        "word_cache_size": current_app.cache_service.cache_size(),
    })


@api_bp.get("/debug/room/<room_code>/players")
def debug_players(room_code: str):
    
    room_svc = current_app.room_service
    room = room_svc._rooms.get_by_code(room_code.upper())
    if not room:
        return jsonify({"error": "not found"}), 404
    players = [
        {"id": p.id, "nickname": p.nickname, "socket_id": p.socket_id,
         "is_host": p.is_host, "connected": p.connected}
        for p in room.players.values()
    ]
    return jsonify({"room_id": room.id, "state": room.state.value, "players": players})


@api_bp.post("/debug/room/<room_code>/start")
def debug_start_game(room_code: str):
    
    room_svc = current_app.room_service
    game_svc = current_app.game_service
    room = room_svc._rooms.get_by_code(room_code.upper())
    if not room:
        return jsonify({"error": "not found"}), 404
    host = room.players.get(room.host_id)
    if not host:
        return jsonify({"error": "no host"}), 400
    try:
        room2, game = game_svc.start_game(host.id)
        return jsonify({"ok": True, "word": game.word, "state": room2.state.value})
    except Exception as e:
        logger.exception("debug start_game failed")
        return jsonify({"error": str(e)}), 500


@api_bp.get("/room/<room_code>")
def room_info(room_code: str):
    room_svc = current_app.room_service
    room = room_svc._rooms.get_by_code(room_code.upper())
    if not room:
        return jsonify({"error": "Sala no encontrada"}), 404
    return jsonify({
        "code": room.code,
        "state": room.state.value,
        "player_count": room.player_count,
        "settings": room.settings.to_dict(),
    })
