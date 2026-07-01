import os


class Config:
    SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-in-production")
    FLASK_ENV: str = os.getenv("FLASK_ENV", "production")

    # Room lifecycle
    ROOM_EXPIRY_SECONDS: int = int(os.getenv("ROOM_EXPIRY_SECONDS", 7200))
    MAX_PLAYERS_PER_ROOM: int = int(os.getenv("MAX_PLAYERS_PER_ROOM", 8))
    CLEANUP_INTERVAL_SECONDS: int = int(os.getenv("CLEANUP_INTERVAL_SECONDS", 60))

    # Player reconnection window
    RECONNECT_WINDOW_SECONDS: int = 60

    # Game settings bounds
    WORD_LENGTH_MIN: int = 5
    WORD_LENGTH_MAX: int = 5
    MAX_ATTEMPTS_MIN: int = 6
    MAX_ATTEMPTS_MAX: int = 6

    # RAE API
    RAE_TIMEOUT_SECONDS: int = int(os.getenv("RAE_TIMEOUT_SECONDS", 5))
    RAE_SEARCH_URL: str = "https://dle.rae.es/data/search"
    RAE_HEADERS: dict = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "es-ES,es;q=0.9",
        "Referer": "https://dle.rae.es/",
        "X-Requested-With": "XMLHttpRequest",
    }

    # Rate limiting: max guesses per player per minute
    GUESS_RATE_LIMIT: int = 20

    # Socket.IO
    SOCKETIO_ASYNC_MODE: str = "threading"
    SOCKETIO_CORS_ALLOWED_ORIGINS: str = "*"
    SOCKETIO_PING_TIMEOUT: int = 20
    SOCKETIO_PING_INTERVAL: int = 10

    @classmethod
    def is_development(cls) -> bool:
        return cls.FLASK_ENV == "development"
