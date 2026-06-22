from abc import ABC, abstractmethod
from typing import List, Optional
from pathlib import Path

class Uploader(ABC):
    @abstractmethod
    def upload(self, file_paths: Optional[List[Path]] = None) -> None:
        """Upload a list of files to the target destination."""
        pass
