from src.utils.factory import Registry
from .base import Uploader

_uploader_registry = Registry[Uploader]("uploader")

register_uploader = _uploader_registry.register
create_uploader = _uploader_registry.create
