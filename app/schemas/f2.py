from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.f2 import SessionType, SessionStatus, ResultStatus, PenaltyType


# --- Season ---


class SeasonBase(BaseModel):
    year: int


class SeasonCreate(SeasonBase):
    pass


class SeasonResponse(SeasonBase):
    id: int

    model_config = {"from_attributes": True}


# --- Round ---


class RoundBase(BaseModel):
    round_number: int
    name: str
    circuit_name: str
    city: str
    country: str
    timezone: str


class RoundCreate(RoundBase):
    season_id: int


class RoundResponse(RoundBase):
    id: int
    season_id: int

    model_config = {"from_attributes": True}


# --- Session ---


class SessionBase(BaseModel):
    type: SessionType
    scheduled_at_utc: datetime
    status: SessionStatus
    is_reversed_grid: bool = False


class SessionCreate(SessionBase):
    round_id: int


class SessionResponse(SessionBase):
    id: int
    round_id: int

    model_config = {"from_attributes": True}


# --- Driver ---


class DriverBase(BaseModel):
    first_name: str
    last_name: str
    nationality: str
    number: int


class DriverCreate(DriverBase):
    pass


class DriverResponse(DriverBase):
    id: int

    model_config = {"from_attributes": True}


# --- Team ---


class TeamBase(BaseModel):
    name: str
    nationality: str


class TeamCreate(TeamBase):
    pass


class TeamResponse(TeamBase):
    id: int

    model_config = {"from_attributes": True}


# --- DriverSeasonEntry ---


class DriverSeasonEntryBase(BaseModel):
    driver_id: int
    team_id: int
    season_id: int
    from_round: Optional[int] = None


class DriverSeasonEntryCreate(DriverSeasonEntryBase):
    pass


class DriverSeasonEntryResponse(DriverSeasonEntryBase):
    id: int

    model_config = {"from_attributes": True}


# --- Result ---


class ResultBase(BaseModel):
    session_id: int
    driver_id: int
    team_id: int
    grid_position: Optional[int] = None
    finish_position: Optional[int] = None
    status: ResultStatus
    points: int = 0
    has_fastest_lap: bool = False
    fastest_lap_time: Optional[str] = None


class ResultCreate(ResultBase):
    pass


class ResultResponse(ResultBase):
    id: int

    model_config = {"from_attributes": True}


# --- Penalty ---


class PenaltyBase(BaseModel):
    result_id: int
    type: PenaltyType
    description: str
    applied: bool = False


class PenaltyCreate(PenaltyBase):
    pass


class PenaltyResponse(PenaltyBase):
    id: int

    model_config = {"from_attributes": True}
