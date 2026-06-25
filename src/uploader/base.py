import json
from abc import ABC, abstractmethod
from typing import Union, List, Dict, Tuple, Optional
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
            
        for filename, info in list(stage_data.items()):
            stage_updated = False
            if not isinstance(info, dict):
                status = info
                file_id = None
            else:
                status = info.get("status")
                file_id = info.get("file_id")

            filepath = config.ARTICLES_DIR / filename
            
            if status == "New":
                if not filepath.exists():
                    continue
                new_id = self.execute_new(filename)
                if new_id:
                    stage_data[filename] = {"status": "Synced", "file_id": new_id}
                    stage_updated = True
                    
            elif status == "Modified":
                if not filepath.exists():
                    continue
                if file_id:
                    new_id = self.execute_update(filename, file_id)
                else:
                    new_id = self.execute_new(filename)
                
                if new_id:
                    stage_data[filename] = {"status": "Synced", "file_id": new_id}
                    stage_updated = True
                    
            elif status == "Deleted":
                if file_id:
                    success = self.execute_delete(filename, file_id)
                else:
                    success = True
                
                if success:
                    del stage_data[filename]
                    stage_updated = True

            if stage_updated:
                with open(stage_path, "w") as f:
                    json.dump(stage_data, f, indent=4)

    @abstractmethod
    def execute_new(self, filename: str) -> Optional[str]:
        """Execute logic to upload a new file. Returns the new file_id or None on failure."""
        pass

    @abstractmethod
    def execute_update(self, filename: str, file_id: str) -> Optional[str]:
        """Execute logic to update an existing file. Returns the new file_id or None on failure."""
        pass

    @abstractmethod
    def execute_delete(self, filename: str, file_id: str) -> bool:
        """Execute logic to delete an existing file. Returns True on success."""
        pass
