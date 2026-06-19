from sqlalchemy.orm import Session

from app.models.f2 import Season, Round
from app.schemas.f2 import SeasonCreate, RoundCreate


# --- Season CRUD ---


def get_seasons(db: Session) -> list[Season]:
    return db.query(Season).all()


def get_season(db: Session, season_id: int) -> Season | None:
    return db.query(Season).filter(Season.id == season_id).first()


def get_season_by_year(db: Session, year: int) -> Season | None:
    return db.query(Season).filter(Season.year == year).first()


def create_season(db: Session, season: SeasonCreate) -> Season:
    db_season = Season(year=season.year)
    db.add(db_season)
    db.commit()
    db.refresh(db_season)
    return db_season


# --- Round CRUD ---


def get_rounds(db: Session, season_id: int | None = None) -> list[Round]:
    query = db.query(Round)
    if season_id is not None:
        query = query.filter(Round.season_id == season_id)
    return query.order_by(Round.round_number).all()


def get_round(db: Session, round_id: int) -> Round | None:
    return db.query(Round).filter(Round.id == round_id).first()


def create_round(db: Session, round_data: RoundCreate) -> Round:
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
