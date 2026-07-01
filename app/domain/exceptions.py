class WordleRaceError(Exception):
    """Base exception for all domain errors."""
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str, code: str | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message}


class RoomNotFoundError(WordleRaceError):
    code = "ROOM_NOT_FOUND"

    def __init__(self, identifier: str):
        super().__init__(f"Sala '{identifier}' no encontrada.")


class RoomFullError(WordleRaceError):
    code = "ROOM_FULL"

    def __init__(self):
        super().__init__("La sala está llena.")


class RoomNotInStateError(WordleRaceError):
    code = "ROOM_INVALID_STATE"

    def __init__(self, expected: str, actual: str):
        super().__init__(
            f"La sala debe estar en estado '{expected}', pero está en '{actual}'."
        )


class PlayerNotFoundError(WordleRaceError):
    code = "PLAYER_NOT_FOUND"

    def __init__(self, player_id: str):
        super().__init__(f"Jugador '{player_id}' no encontrado.")


class NotHostError(WordleRaceError):
    code = "NOT_HOST"

    def __init__(self):
        super().__init__("Solo el anfitrión puede realizar esta acción.")


class GameNotActiveError(WordleRaceError):
    code = "GAME_NOT_ACTIVE"

    def __init__(self):
        super().__init__("No hay un juego activo en esta sala.")


class AlreadyFinishedError(WordleRaceError):
    code = "ALREADY_FINISHED"

    def __init__(self):
        super().__init__("Ya terminaste el juego.")


class InvalidWordError(WordleRaceError):
    code = "INVALID_WORD"

    def __init__(self, word: str):
        super().__init__(
            f"'{word}' no es una palabra válida."
        )


class WrongWordLengthError(WordleRaceError):
    code = "WRONG_WORD_LENGTH"

    def __init__(self, expected: int, got: int):
        super().__init__(
            f"La palabra debe tener {expected} letras (recibida: {got})."
        )


class InvalidSettingsError(WordleRaceError):
    code = "INVALID_SETTINGS"


class RateLimitError(WordleRaceError):
    code = "RATE_LIMIT"

    def __init__(self):
        super().__init__("Demasiados intentos. Espera un momento.")


class NicknameRequiredError(WordleRaceError):
    code = "NICKNAME_REQUIRED"

    def __init__(self):
        super().__init__("El apodo no puede estar vacío.")


class NoWordsAvailableError(WordleRaceError):
    code = "NO_WORDS_AVAILABLE"

    def __init__(self, length: int):
        super().__init__(f"No hay palabras de {length} letras disponibles.")
