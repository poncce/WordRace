
import logging
import threading
import time

from flask import Flask, send_from_directory
from flask_socketio import SocketIO

from app.config import Config
from app.repositories.memory import (
    MemoryPlayerRepository,
    MemoryRoomRepository,
    MemoryWordCacheRepository,
)
from app.services.cache_service import CacheService
from app.services.game_service import GameService
from app.services.room_service import RoomService
from app.services.word_service import WordValidationService
from app.sockets.handlers import register_handlers
from app.api.routes import api_bp

socketio = SocketIO(
    async_mode=Config.SOCKETIO_ASYNC_MODE,
    cors_allowed_origins=Config.SOCKETIO_CORS_ALLOWED_ORIGINS,
    ping_timeout=Config.SOCKETIO_PING_TIMEOUT,
    ping_interval=Config.SOCKETIO_PING_INTERVAL,
    logger=False,
    engineio_logger=False,
)


def create_app() -> Flask:
    app = Flask(__name__, static_folder="static", static_url_path="/static")
    app.config["SECRET_KEY"] = Config.SECRET_KEY

    _configure_logging(app)

    
    room_repo = MemoryRoomRepository()
    player_repo = MemoryPlayerRepository()
    word_cache_repo = MemoryWordCacheRepository()

    cache_svc = CacheService(word_cache_repo)
    word_svc = WordValidationService(cache_svc)
    room_svc = RoomService(room_repo, player_repo)
    game_svc = GameService(room_repo, player_repo, word_svc)

    
    app.room_service = room_svc
    app.game_service = game_svc
    app.cache_service = cache_svc

    
    app.register_blueprint(api_bp)

    
    socketio.init_app(app)
    register_handlers(socketio, room_svc, game_svc)

    
    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    @app.get("/join/<room_code>")
    def join_link(room_code: str):
        return send_from_directory(app.static_folder, "index.html")

    
    _start_cleanup_task(app, room_svc)

    return app


def _configure_logging(app: Flask) -> None:
    level = logging.DEBUG if Config.is_development() else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app.logger.setLevel(level)


def _start_cleanup_task(app: Flask, room_svc: RoomService) -> None:
    interval = Config.CLEANUP_INTERVAL_SECONDS

    def cleanup_loop():
        while True:
            time.sleep(interval)
            with app.app_context():
                try:
                    expired = room_svc.cleanup_expired_rooms()
                    ghosts = room_svc.cleanup_ghost_players()
                    if expired or ghosts:
                        logging.getLogger(__name__).info(
                            "Cleanup: %d expired rooms, %d ghost players removed",
                            expired, ghosts,
                        )
                except Exception as exc:
                    logging.getLogger(__name__).error("Cleanup error: %s", exc)

    t = threading.Thread(target=cleanup_loop, daemon=True)
    t.start()
