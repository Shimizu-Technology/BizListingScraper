"""Pydantic models for API request/response."""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ListingBase(BaseModel):
    external_id: str
    source: str = "bizbuysell"
    url: str
    title: str
    asking_price: Optional[float] = None
    cash_flow: Optional[float] = None
    gross_revenue: Optional[float] = None
    ebitda: Optional[float] = None
    city: Optional[str] = None
    state: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    broker_name: Optional[str] = None
    broker_company: Optional[str] = None

class ListingResponse(ListingBase):
    id: int
    first_seen_at: datetime
    last_seen_at: datetime
    last_updated_at: Optional[datetime] = None
    is_active: bool = True
    is_new_today: bool = False
    has_price_change: bool = False
    is_reviewed: bool = False
    reviewed_at: Optional[datetime] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True

class ReviewUpdate(BaseModel):
    is_reviewed: bool
    notes: Optional[str] = None

class ListingsResponse(BaseModel):
    listings: list[ListingResponse]
    total: int
    page: int
    per_page: int
    pages: int

class StatsResponse(BaseModel):
    total_active_listings: int
    new_today: int
    updated_today: int
    removed_this_week: int
    avg_asking_price: float
    total_value: float
    listings_by_category: dict
    listings_by_state: dict

class HistoryEntry(BaseModel):
    id: int
    changed_at: datetime
    change_type: str
    old_values: Optional[dict] = None
    new_values: Optional[dict] = None
    changed_fields: Optional[list[str]] = None

class ScrapeRunResponse(BaseModel):
    id: int
    source: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    pages_scraped: int
    listings_found: int
    listings_inserted: int
    listings_updated: int
    listings_unchanged: int
    listings_deactivated: int
    error_message: Optional[str] = None
