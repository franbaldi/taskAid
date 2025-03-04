# backend/models.py
from pydantic import BaseModel
from typing import List, Optional

class ServiceCompany(BaseModel):
    google_maps_id: str
    address: str
    last_updated: str
    name: str
    phone: str
    price_level: Optional[str] = None
    rating: float
    reviews: List[str]
    types: List[str]
    website: Optional[str] = None
    embeddings: Optional[List[float]] = None
