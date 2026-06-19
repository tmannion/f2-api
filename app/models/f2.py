from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.database import Base


class SessionType(enum.Enum):
    PRACTICE_1 = "PRACTICE_1"
    PRACTICE_2 = "PRACTICE_2"
    QUALIFYING = "QUALIFYING"
    SPRINT = "SPRINT"
    FEATURE = "FEATURE"


class SessionStatus(enum.Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ResultStatus(enum.Enum):
    FINISHED = "FINISHED"
    DNF = "DNF"
    DNS = "DNS"
    DSQ = "DSQ"
    CLASSIFIED = "CLASSIFIED"


class PenaltyType(enum.Enum):
    TIME = "TIME"
    GRID = "GRID"
    DISQUALIFICATION = "DISQUALIFICATION"
    REPRIMAND = "REPRIMAND"


class Season(Base):
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(unique=True)

    rounds: Mapped[list["Round"]] = relationship(back_populates="season")
    entries: Mapped[list["DriverSeasonEntry"]] = relationship(back_populates="season")


class Round(Base):
    __tablename__ = "rounds"

    id: Mapped[int] = mapped_column(primary_key=True)
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"))
    round_number: Mapped[int] = mapped_column()
    name: Mapped[str] = mapped_column(String)
    circuit_name: Mapped[str] = mapped_column(String)
    city: Mapped[str] = mapped_column(String)
    country: Mapped[str] = mapped_column(String)
    timezone: Mapped[str] = mapped_column(String)  # IANA e.g. "Asia/Bahrain"

    season: Mapped["Season"] = relationship(back_populates="rounds")
    sessions: Mapped[list["Session"]] = relationship(back_populates="round")


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    round_id: Mapped[int] = mapped_column(ForeignKey("rounds.id"))
    type: Mapped[SessionType] = mapped_column(Enum(SessionType))
    scheduled_at_utc: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus), default=SessionStatus.SCHEDULED
    )
    is_reversed_grid: Mapped[bool] = mapped_column(default=False)

    round: Mapped["Round"] = relationship(back_populates="sessions")
    results: Mapped[list["Result"]] = relationship(back_populates="session")


class Driver(Base):
    __tablename__ = "drivers"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    nationality: Mapped[str] = mapped_column(String)
    number: Mapped[int] = mapped_column()

    season_entries: Mapped[list["DriverSeasonEntry"]] = relationship(
        back_populates="driver"
    )
    results: Mapped[list["Result"]] = relationship(back_populates="driver")


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    nationality: Mapped[str] = mapped_column(String)

    season_entries: Mapped[list["DriverSeasonEntry"]] = relationship(back_populates="team")
    results: Mapped[list["Result"]] = relationship(back_populates="team")


class DriverSeasonEntry(Base):
    __tablename__ = "driver_season_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    season_id: Mapped[int] = mapped_column(ForeignKey("seasons.id"))
    from_round: Mapped[Optional[int]] = mapped_column(default=None)  # null = present from round 1

    driver: Mapped["Driver"] = relationship(back_populates="season_entries")
    team: Mapped["Team"] = relationship(back_populates="season_entries")
    season: Mapped["Season"] = relationship(back_populates="entries")


class Result(Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"))
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"))
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"))
    grid_position: Mapped[Optional[int]] = mapped_column(default=None)
    finish_position: Mapped[Optional[int]] = mapped_column(default=None)
    status: Mapped[ResultStatus] = mapped_column(Enum(ResultStatus))
    points: Mapped[int] = mapped_column(default=0)
    has_fastest_lap: Mapped[bool] = mapped_column(default=False)
    fastest_lap_time: Mapped[Optional[str]] = mapped_column(
        String, default=None
    )  # e.g. "1:27.452"

    session: Mapped["Session"] = relationship(back_populates="results")
    driver: Mapped["Driver"] = relationship(back_populates="results")
    team: Mapped["Team"] = relationship(back_populates="results")
    penalties: Mapped[list["Penalty"]] = relationship(back_populates="result")


class Penalty(Base):
    __tablename__ = "penalties"

    id: Mapped[int] = mapped_column(primary_key=True)
    result_id: Mapped[int] = mapped_column(ForeignKey("results.id"))
    type: Mapped[PenaltyType] = mapped_column(Enum(PenaltyType))
    description: Mapped[str] = mapped_column(String)
    applied: Mapped[bool] = mapped_column(default=False)

    result: Mapped["Result"] = relationship(back_populates="penalties")
