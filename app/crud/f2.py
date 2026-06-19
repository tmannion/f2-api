from sqlalchemy.orm import Session as DBSession

from app.models.f2 import (
    Season,
    Round,
    Session,
    Driver,
    Team,
    DriverSeasonEntry,
    Result,
    Penalty,
)
from app.schemas.f2 import (
    SeasonCreate,
    RoundCreate,
    SessionCreate,
    DriverCreate,
    TeamCreate,
    DriverSeasonEntryCreate,
    ResultCreate,
    PenaltyCreate,
)


# --- Season CRUD ---


def get_seasons(db: DBSession) -> list[Season]:
    return db.query(Season).all()


def get_season(db: DBSession, season_id: int) -> Season | None:
    return db.query(Season).filter(Season.id == season_id).first()


def get_season_by_year(db: DBSession, year: int) -> Season | None:
    return db.query(Season).filter(Season.year == year).first()


def create_season(db: DBSession, season: SeasonCreate) -> Season:
    db_season = Season(year=season.year)
    db.add(db_season)
    db.commit()
    db.refresh(db_season)
    return db_season


# --- Round CRUD ---


def get_rounds(db: DBSession, season_id: int | None = None) -> list[Round]:
    query = db.query(Round)
    if season_id is not None:
        query = query.filter(Round.season_id == season_id)
    return query.order_by(Round.round_number).all()


def get_round(db: DBSession, round_id: int) -> Round | None:
    return db.query(Round).filter(Round.id == round_id).first()


def create_round(db: DBSession, round_data: RoundCreate) -> Round:
    db_round = Round(
        season_id=round_data.season_id,
        round_number=round_data.round_number,
        name=round_data.name,
        circuit_name=round_data.circuit_name,
        city=round_data.city,
        country=round_data.country,
        timezone=round_data.timezone,
    )
    db.add(db_round)
    db.commit()
    db.refresh(db_round)
    return db_round


# --- Session CRUD ---


def get_sessions(db: DBSession, round_id: int | None = None) -> list[Session]:
    query = db.query(Session)
    if round_id is not None:
        query = query.filter(Session.round_id == round_id)
    return query.order_by(Session.scheduled_at_utc).all()


def get_session(db: DBSession, session_id: int) -> Session | None:
    return db.query(Session).filter(Session.id == session_id).first()


def create_session(db: DBSession, session_data: SessionCreate) -> Session:
    db_session = Session(
        round_id=session_data.round_id,
        type=session_data.type,
        scheduled_at_utc=session_data.scheduled_at_utc,
        status=session_data.status,
        is_reversed_grid=session_data.is_reversed_grid,
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


# --- Driver CRUD ---


def get_drivers(db: DBSession) -> list[Driver]:
    return db.query(Driver).order_by(Driver.last_name).all()


def get_driver(db: DBSession, driver_id: int) -> Driver | None:
    return db.query(Driver).filter(Driver.id == driver_id).first()


def create_driver(db: DBSession, driver_data: DriverCreate) -> Driver:
    db_driver = Driver(
        first_name=driver_data.first_name,
        last_name=driver_data.last_name,
        nationality=driver_data.nationality,
        number=driver_data.number,
    )
    db.add(db_driver)
    db.commit()
    db.refresh(db_driver)
    return db_driver


# --- Team CRUD ---


def get_teams(db: DBSession) -> list[Team]:
    return db.query(Team).order_by(Team.name).all()


def get_team(db: DBSession, team_id: int) -> Team | None:
    return db.query(Team).filter(Team.id == team_id).first()


def create_team(db: DBSession, team_data: TeamCreate) -> Team:
    db_team = Team(
        name=team_data.name,
        nationality=team_data.nationality,
    )
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team


# --- DriverSeasonEntry CRUD ---


def get_entries(
    db: DBSession, season_id: int | None = None, driver_id: int | None = None
) -> list[DriverSeasonEntry]:
    query = db.query(DriverSeasonEntry)
    if season_id is not None:
        query = query.filter(DriverSeasonEntry.season_id == season_id)
    if driver_id is not None:
        query = query.filter(DriverSeasonEntry.driver_id == driver_id)
    return query.all()


def get_entry(db: DBSession, entry_id: int) -> DriverSeasonEntry | None:
    return db.query(DriverSeasonEntry).filter(DriverSeasonEntry.id == entry_id).first()


def create_entry(
    db: DBSession, entry_data: DriverSeasonEntryCreate
) -> DriverSeasonEntry:
    db_entry = DriverSeasonEntry(
        driver_id=entry_data.driver_id,
        team_id=entry_data.team_id,
        season_id=entry_data.season_id,
        from_round=entry_data.from_round,
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)
    return db_entry


# --- Result CRUD ---


def get_results(
    db: DBSession, session_id: int | None = None, driver_id: int | None = None
) -> list[Result]:
    query = db.query(Result)
    if session_id is not None:
        query = query.filter(Result.session_id == session_id)
    if driver_id is not None:
        query = query.filter(Result.driver_id == driver_id)
    return query.order_by(Result.finish_position).all()


def get_result(db: DBSession, result_id: int) -> Result | None:
    return db.query(Result).filter(Result.id == result_id).first()


def create_result(db: DBSession, result_data: ResultCreate) -> Result:
    db_result = Result(
        session_id=result_data.session_id,
        driver_id=result_data.driver_id,
        team_id=result_data.team_id,
        grid_position=result_data.grid_position,
        finish_position=result_data.finish_position,
        status=result_data.status,
        points=result_data.points,
        has_fastest_lap=result_data.has_fastest_lap,
        fastest_lap_time=result_data.fastest_lap_time,
    )
    db.add(db_result)
    db.commit()
    db.refresh(db_result)
    return db_result


# --- Penalty CRUD ---


def get_penalties(db: DBSession, result_id: int | None = None) -> list[Penalty]:
    query = db.query(Penalty)
    if result_id is not None:
        query = query.filter(Penalty.result_id == result_id)
    return query.all()


def get_penalty(db: DBSession, penalty_id: int) -> Penalty | None:
    return db.query(Penalty).filter(Penalty.id == penalty_id).first()


def create_penalty(db: DBSession, penalty_data: PenaltyCreate) -> Penalty:
    db_penalty = Penalty(
        result_id=penalty_data.result_id,
        type=penalty_data.type,
        description=penalty_data.description,
        applied=penalty_data.applied,
    )
    db.add(db_penalty)
    db.commit()
    db.refresh(db_penalty)
    return db_penalty
