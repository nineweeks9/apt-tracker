from pydantic import BaseModel
from typing import Optional

class FolderCreate(BaseModel):
    name: str

class ApartmentCreate(BaseModel):
    apt_name: str
    sigungu_code: str
    dong: Optional[str] = None
    sigungu_name: Optional[str] = None
    folder_id: Optional[int] = None
