from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Union
from pathlib import Path

class Uploader(ABC):
    @abstractmethod
    def upload(self, file_data: Optional[Union[Dict[str, List[Path]], List[Path]]] = None) -> None:
        """Upload a list of files or dictionary of added/updated files to the target destination."""
        pass
