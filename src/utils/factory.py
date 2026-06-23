from typing import Dict, Type, Callable, TypeVar, Generic, Any

T = TypeVar('T')

class Registry(Generic[T]):
    def __init__(self, item_type_name: str):
        self._registry: Dict[str, Type[T]] = {}
        self.item_type_name = item_type_name

    def register(self, *names: str) -> Callable:
        """Decorator to register a class under one or more names."""
        def decorator(cls: Type[T]):
            for name in names:
                self._registry[name.lower()] = cls
            return cls
        return decorator

    def create(self, provider: str, **kwargs: Any) -> T:
        """Create a new instance based on the provider name."""
        provider_lower = provider.lower()
        if provider_lower not in self._registry:
            raise ValueError(f"Unsupported {self.item_type_name} provider: {provider}")
        
        target_class = self._registry[provider_lower]
        return target_class(**kwargs)

    def copy(self) -> Dict[str, Type[T]]:
        return self._registry.copy()

    def clear(self) -> None:
        self._registry.clear()

    def update(self, other: Dict[str, Type[T]]) -> None:
        self._registry.update(other)

    def __contains__(self, key: str) -> bool:
        return key in self._registry

    def __getitem__(self, key: str) -> Type[T]:
        return self._registry[key]
