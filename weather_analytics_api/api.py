from fastapi import FastAPI

from weather_analytics_api.routers import auth, weather

app = FastAPI(title="Weather Analytics API", version="1.0")

# Auth endpoints
app.include_router(auth.router, prefix="/auth", tags=["auth"])

# Weather endpoints
# GET /api/weather -> get_weather
# GET /api/weather/stats -> get_weather_stats
app.include_router(weather.router, prefix="/api/weather", tags=["weather"])
