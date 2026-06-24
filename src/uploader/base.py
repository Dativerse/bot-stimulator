from abc import ABC, abstractmethod
from typing import Union
from pathlib import Path

class Uploader(ABC):
    @abstractmethod
    def upload(self, stage_file: Union[Path, str]) -> None:
        """Upload markdown articles to the target destination based on a stage file."""
        pass
