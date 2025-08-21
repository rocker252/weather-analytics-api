from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, field_validator

T = TypeVar("T")


class WeatherOut(BaseModel):
    station_id: str
    date: str
    max_temp: Optional[float]
    min_temp: Optional[float]
    precipitation: Optional[float]

    model_config = {"from_attributes": True}  # Replaces Config.orm_mode

    @field_validator("date", mode="before")
    @classmethod
    def format_date(cls, v):
        return v.strftime("%Y-%m-%d") if hasattr(v, "strftime") else v


class WeatherStatsOut(BaseModel):
    station_id: str
    year: int
    avg_max_temp: Optional[float]
    avg_min_temp: Optional[float]
    total_precipitation: Optional[float]

    model_config = {"from_attributes": True}


class PaginationInfo(BaseModel):
    page: int
    limit: int
    total: int
    pages: int


class PaginatedResponse(BaseModel, Generic[T]):
    data: List[T]
    pagination: PaginationInfo
