from app.repositories.base import AbstractWordCacheRepository


class CacheService:
    """Thin service wrapper over the word validity cache repository."""

    def __init__(self, cache_repo: AbstractWordCacheRepository):
        self._repo = cache_repo

    def get_word_validity(self, word: str) -> bool | None:
        return self._repo.get(word)

    def set_word_validity(self, word: str, valid: bool) -> None:
        self._repo.set(word, valid)

    def cache_size(self) -> int:
        return self._repo.size()
