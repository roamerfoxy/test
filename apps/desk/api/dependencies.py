from functools import lru_cache
from apps.desk.services.desk import DeskService


@lru_cache
def get_desk_service() -> DeskService:
    """
    Dependency provider for DeskService.
    Uses lru_cache to ensure a singleton instance per application lifecycle,
    mimicking the previous global variable behavior but in a testable way.
    """
    return DeskService()
