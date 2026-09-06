from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BirthDetails(BaseModel):
    date: str = Field(..., description="Birth date in YYYY-MM-DD format")
    time: str = Field(..., description="Birth time in HH:MM format (24-hour)")
    place: str = Field(..., description="Birthplace name")
    ayanamsa: Optional[str] = Field(default="lahiri", description="Ayanamsa to use")


class BirthData(BaseModel):
    date: str = Field(..., description="Birth date in YYYY-MM-DD format")
    time: str = Field(..., description="Birth time in HH:MM format (24-hour)")
    place: str = Field(..., description="Birthplace name")
    ayanamsa: Optional[str] = Field(default="lahiri", description="Ayanamsa to use")


class PlaceResult(BaseModel):
    place: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timezone: Optional[str] = None
    source: str = "geopy"
    status: str = "UNRESOLVED"


class ValidationCheck(BaseModel):
    name: str
    passed: bool
    detail: Optional[str] = None


class ValidationResult(BaseModel):
    passed: bool
    checks: List[ValidationCheck]


class PlanetData(BaseModel):
    name: str
    longitude: float
    sign: str
    house: int
    degree: float
    nakshatra: Optional[str] = None
    pada: Optional[int] = None
    source: str = "Swiss Ephemeris"
    status: str = "CALCULATED"


class HouseData(BaseModel):
    number: int
    sign: str
    cusp_longitude: float


class AscendantData(BaseModel):
    longitude: float
    sign: str
    house: int = 1
    degree: float


class Chart(BaseModel):
    status: str
    reason: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    birth: Optional[Dict[str, Any]] = None
    ascendant: Optional[Dict[str, Any]] = None
    planets: Optional[List[PlanetData]] = None
    houses: Optional[List[Dict[str, Any]]] = None
    validation: Optional[Dict[str, Any]] = None
    debug: Optional[Dict[str, Any]] = None


class ChartResponse(BaseModel):
    status: str
    reason: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    birth: Optional[Dict[str, Any]] = None
    ascendant: Optional[AscendantData] = None
    planets: Optional[List[PlanetData]] = None
    houses: Optional[List[HouseData]] = None
    validation: Optional[ValidationResult] = None
    debug: Optional[str] = None
    extra_planets: Optional[List[PlanetData]] = None