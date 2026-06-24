import json
from abc import ABC, abstractmethod
from typing import Union, List
from pathlib import Path
from src import config

class Uploader(ABC):
    def upload(self, stage_file: Union[Path, str]) -> None:
        """Upload markdown articles to the target destination based on a stage file."""
        stage_path = Path(stage_file)
        if not stage_path.exists():
            print(f"Error: Stage file '{stage_file}' not found.")
            return
        
        with open(stage_path, "r") as f:
            stage_data = json.load(f)
            
        files_to_upload = []
        files_to_delete = []

        for filename, status in stage_data.items():
            filepath = config.ARTICLES_DIR / filename
            
            if status in ("New", "Modified"):
                if not filepath.exists():
                    continue
                files_to_upload.append(filepath)
                if status == "Modified":
                    files_to_delete.append(filename)
            elif status == "Deleted":
                files_to_delete.append(filename)

        successfully_deleted = self._execute_sync(files_to_upload, files_to_delete)

        if successfully_deleted:
            for filename in successfully_deleted:
                if stage_data.get(filename) == "Deleted":
                    del stage_data[filename]
            
            with open(stage_path, "w") as f:
                json.dump(stage_data, f, indent=4)

    @abstractmethod
    def _execute_sync(self, files_to_upload: List[Path], files_to_delete: List[str]) -> List[str]:
        """
        Execute the upload and delete operations.
        Returns a list of filenames that were successfully deleted (or didn't exist anymore).
        """
        pass
