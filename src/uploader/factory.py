from typing import Dict, Type, Callable
from .base import Uploader

_uploader_registry: Dict[str, Type[Uploader]] = {}

def register_uploader(*names: str) -> Callable:
    """Decorator to register an uploader class under one or more names."""
    def decorator(cls: Type[Uploader]):
        for name in names:
            _uploader_registry[name.lower()] = cls
        return cls
    return decorator

def create_uploader(provider: str) -> Uploader:
    """Create a new uploader instance based on the provider name."""
    provider_lower = provider.lower()
    if provider_lower not in _uploader_registry:
        raise ValueError(f"Unsupported uploader provider: {provider}")
    
    uploader_class = _uploader_registry[provider_lower]
    return uploader_class()
