from sqlalchemy import Column, Date, Float, Integer, String, UniqueConstraint

from .db import Base

# We want to prevent duplicate rows for the same station and date, which matches your ingestion requirement.
# That is why added unique contstraints


class Weather(Base):
    __tablename__ = "weather"
    __table_args__ = (UniqueConstraint("station_id", "date", name="uix_station_date"),)

    id = Column(Integer, primary_key=True)
    station_id = Column(String, index=True)
    date = Column(Date)
    max_temp = Column(Float)
    min_temp = Column(Float)
    precipitation = Column(Float)


class WeatherStats(Base):
    __tablename__ = "weather_stats"
    __table_args__ = (UniqueConstraint("station_id", "year", name="uix_station_year"),)

    id = Column(Integer, primary_key=True)
    station_id = Column(String, index=True)
    year = Column(Integer, index=True)
    avg_max_temp = Column(Float)
    avg_min_temp = Column(Float)
    total_precipitation = Column(Float)
