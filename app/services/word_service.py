"""
WordValidationService: RAE lookup, word normalization, guess evaluation.

Normalization rules:
  - Convert to uppercase
  - Strip diacritics (accents) EXCEPT Ñ, which is preserved as a distinct letter
  - This lets players type LIMON and match LIMÓN, but CANON ≠ CAÑON
"""
from __future__ import annotations
import logging
import random
import unicodedata
from typing import TYPE_CHECKING

import requests

from app.config import Config
from app.data.words import ALL_WORDS, VALID_GUESSES, WORDS_BY_LENGTH
from app.domain.exceptions import InvalidWordError, NoWordsAvailableError, WrongWordLengthError
from app.domain.models import GuessRecord, TileResult, TileState

if TYPE_CHECKING:
    from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)


def normalize(word: str) -> str:
    """Uppercase + strip accents, keeping Ñ."""
    word = word.upper().strip()
    result: list[str] = []
    for char in word:
        if char == "Ñ":
            result.append("Ñ")
        else:
            nfkd = unicodedata.normalize("NFKD", char)
            base = "".join(c for c in nfkd if unicodedata.category(c) != "Mn")
            result.append(base)
    return "".join(result)


class WordValidationService:
    def __init__(self, cache_service: CacheService):
        self._cache = cache_service

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def validate_and_evaluate(
        self, guess: str, target: str, expected_length: int
    ) -> GuessRecord:
        """
        Validate the guess (length + RAE), evaluate against the target,
        and return a GuessRecord. Raises domain exceptions on failure.
        """
        norm_guess = normalize(guess)
        norm_target = normalize(target)

        if len(norm_guess) != expected_length:
            raise WrongWordLengthError(expected_length, len(norm_guess))

        if not self._is_valid(norm_guess):
            raise InvalidWordError(guess)

        tiles = self._evaluate(norm_guess, norm_target)
        return GuessRecord(word=norm_guess, tiles=tiles)

    def get_random_word(self, length: int) -> str:
        words = WORDS_BY_LENGTH.get(length)
        if not words:
            raise NoWordsAvailableError(length)
        word = random.choice(words)
        # Pre-warm cache: these words are always valid
        self._cache.set_word_validity(word, True)
        return word

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    _VALID_CHARS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZÑ")

    def _is_valid(self, word: str) -> bool:
        # Must contain only Spanish alphabet characters (no numbers, symbols, etc.)
        if not all(c in self._VALID_CHARS for c in word):
            return False
        # Reject trivially invalid strings (all identical characters)
        if len(set(word)) == 1:
            return False

        cached = self._cache.get_word_validity(word)
        if cached is not None:
            return cached

        # Words in our local corpus are always valid (no API call needed)
        if word in VALID_GUESSES:
            self._cache.set_word_validity(word, True)
            return True

        # Fall back to Wiktionary API (free, no auth required)
        try:
            valid = self._query_wiktionary(word.lower())
        except Exception as exc:
            logger.warning("Wiktionary API unreachable for '%s': %s — rejecting word", word, exc)
            valid = False  # Fail closed: unknown words are not accepted

        self._cache.set_word_validity(word, valid)
        return valid

    def _query_wiktionary(self, word: str) -> bool:
        """Check if a word exists in Spanish Wiktionary."""
        response = requests.get(
            "https://es.wiktionary.org/w/api.php",
            params={
                "action": "query",
                "titles": word,
                "format": "json",
                "prop": "info",
                "redirects": 1,
            },
            timeout=Config.RAE_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        # Wiktionary returns page id -1 when the page doesn't exist
        return not any(pid == "-1" for pid in pages)

    @staticmethod
    def _evaluate(guess: str, target: str) -> list[TileResult]:
        """
        Classic Wordle evaluation:
        1. Mark exact matches as CORRECT and remove them from consideration.
        2. Mark remaining letters that appear elsewhere as PRESENT.
        3. Everything else is ABSENT.
        """
        n = len(target)
        result = [TileState.ABSENT] * n
        remaining_target: list[str | None] = list(target)
        remaining_guess: list[str | None] = list(guess)

        # Pass 1: correct positions
        for i in range(n):
            if i < len(remaining_guess) and remaining_guess[i] == remaining_target[i]:
                result[i] = TileState.CORRECT
                remaining_target[i] = None
                remaining_guess[i] = None

        # Pass 2: present in wrong position
        for i in range(n):
            g = remaining_guess[i]
            if g is None:
                continue
            if g in remaining_target:
                result[i] = TileState.PRESENT
                remaining_target[remaining_target.index(g)] = None

        return [
            TileResult(letter=guess[i], state=result[i]) for i in range(n)
        ]
