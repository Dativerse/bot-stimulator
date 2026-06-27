from enum import Enum

class SyncStatus(str, Enum):
    NEW = "New"
    MODIFIED = "Modified"
    UPLOADED = "Uploaded"
    SYNCED = "Synced"
    DELETED = "Deleted"
