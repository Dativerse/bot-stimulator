from typing import Dict, Type, Callable
from .base import Fetcher

_fetcher_registry: Dict[str, Type[Fetcher]] = {}

def register_fetcher(*names: str) -> Callable:
    """Decorator to register a fetcher class under one or more names."""
    def decorator(cls: Type[Fetcher]):
        for name in names:
            _fetcher_registry[name.lower()] = cls
        return cls
    return decorator

def create_fetcher(provider: str) -> Fetcher:
    """Create a new fetcher instance based on the provider name."""
    provider_lower = provider.lower()
    if provider_lower not in _fetcher_registry:
        raise ValueError(f"Unsupported fetcher provider: {provider}")
    
    fetcher_class = _fetcher_registry[provider_lower]
    return fetcher_class()
