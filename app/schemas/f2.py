from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.f2 import PenaltyType, ResultStatus, SessionStatus, SessionType


# --- Season ---


class SeasonBase(BaseModel):
    year: int = Field(description="Championship year", examples=[2026])


class SeasonCreate(SeasonBase):
    """Create a new F2 championship season."""


class SeasonResponse(SeasonBase):
    """An F2 championship season."""

    id: int

    model_config = {"from_attributes": True}


# --- Round ---


class RoundBase(BaseModel):
    round_number: int = Field(
        description="Round number within the season", examples=[1]
    )
    name: str = Field(description="Round name", examples=["Melbourne Round"])
    circuit_name: str = Field(
        description="Circuit name", examples=["Albert Park Circuit"]
    )
    city: str = Field(description="Host city", examples=["Melbourne"])
    country: str = Field(description="Host country", examples=["Australia"])
    timezone: str = Field(
        description="IANA timezone for the venue",
        examples=["Australia/Melbourne"],
    )


class RoundCreate(RoundBase):
    """Create a new round within a season."""

    season_id: int = Field(description="ID of the season this round belongs to")


class RoundResponse(RoundBase):
    """A race weekend round."""

    id: int
    season_id: int

    model_config = {"from_attributes": True}


# --- Session ---


class SessionBase(BaseModel):
    type: SessionType = Field(
        description="Session type (QUALIFYING, SPRINT, SPRINT_1, SPRINT_2, FEATURE)",
        examples=["FEATURE"],
    )
    scheduled_at_utc: datetime = Field(
        description="Scheduled start time in UTC",
        examples=["2026-03-08T00:25:00"],
    )
    status: SessionStatus = Field(
        description="Session lifecycle status", examples=["COMPLETED"]
    )
    is_reversed_grid: bool = Field(
        default=False,
        description="Whether this session uses a reversed grid (Sprint races)",
    )


class SessionCreate(SessionBase):
    """Create a new session within a round."""

    round_id: int = Field(description="ID of the round this session belongs to")


class SessionResponse(SessionBase):
    """A race session (qualifying, sprint, or feature race)."""

    id: int
    round_id: int

    model_config = {"from_attributes": True}


# --- Driver ---


class DriverBase(BaseModel):
    first_name: str = Field(description="Driver's first name", examples=["Nikola"])
    last_name: str = Field(description="Driver's last name", examples=["Tsolov"])
    nationality: str = Field(description="Driver's nationality", examples=["Bulgarian"])
    number: int = Field(description="Car number", examples=[6])


class DriverCreate(DriverBase):
    """Register a new driver."""


class DriverResponse(DriverBase):
    """An F2 driver."""

    id: int

    model_config = {"from_attributes": True}


# --- Team ---


class TeamBase(BaseModel):
    name: str = Field(description="Team name", examples=["Campos Racing"])
    nationality: str = Field(description="Team nationality", examples=["Spanish"])


class TeamCreate(TeamBase):
    """Register a new team."""


class TeamResponse(TeamBase):
    """An F2 team."""

    id: int

    model_config = {"from_attributes": True}


# --- DriverSeasonEntry ---


class DriverSeasonEntryBase(BaseModel):
    driver_id: int = Field(description="Driver ID")
    team_id: int = Field(description="Team ID")
    season_id: int = Field(description="Season ID")
    from_round: Optional[int] = Field(
        default=None,
        description="Round number from which this entry is valid (null = full season)",
    )


class DriverSeasonEntryCreate(DriverSeasonEntryBase):
    """Link a driver to a team for a season."""


class DriverSeasonEntryResponse(DriverSeasonEntryBase):
    """A driver's team affiliation for a specific season."""

    id: int

    model_config = {"from_attributes": True}


# --- Result ---


class ResultBase(BaseModel):
    session_id: int = Field(description="ID of the session")
    driver_id: int = Field(description="ID of the driver")
    team_id: int = Field(
        description="ID of the team the driver raced for in this session"
    )
    grid_position: Optional[int] = Field(
        default=None, description="Starting grid position (null for qualifying)"
    )
    finish_position: Optional[int] = Field(
        default=None, description="Final classified position (null for DNF/DNS/DSQ)"
    )
    status: ResultStatus = Field(
        description="Race finish status", examples=["FINISHED"]
    )
    points: int = Field(default=0, description="Points scored in this session")
    has_fastest_lap: bool = Field(
        default=False, description="Whether this driver set the fastest lap"
    )
    fastest_lap_time: Optional[str] = Field(
        default=None,
        description="Fastest lap time as display string",
        examples=["1:31.730"],
    )


class ResultCreate(ResultBase):
    """Record a driver's result for a session."""


class ResultResponse(ResultBase):
    """A driver's result in a specific session."""

    id: int

    model_config = {"from_attributes": True}


# --- Penalty ---


class PenaltyBase(BaseModel):
    result_id: int = Field(description="ID of the result this penalty applies to")
    type: PenaltyType = Field(description="Penalty type", examples=["TIME"])
    description: str = Field(
        description="Human-readable penalty description",
        examples=["5 second time penalty — causing a collision"],
    )
    applied: bool = Field(
        default=False, description="Whether the penalty has been applied to the result"
    )


class PenaltyCreate(PenaltyBase):
    """Record a penalty against a result."""


class PenaltyResponse(PenaltyBase):
    """A penalty issued against a race result."""

    id: int

    model_config = {"from_attributes": True}
