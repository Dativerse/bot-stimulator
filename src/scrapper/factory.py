from src.utils.factory import Registry
from .base import Fetcher

_fetcher_registry = Registry[Fetcher]("fetcher")

register_fetcher = _fetcher_registry.register
create_fetcher = _fetcher_registry.create
