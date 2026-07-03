"""
Import F2 results from a CSV file into the database.

Usage:
    python scripts/import_csv.py seeds/2024_results.csv

CSV columns:
    season_year         - e.g. 2024
    round_number        - e.g. 1
    round_name          - e.g. "Melbourne Round"
    circuit_name        - e.g. "Albert Park Circuit"
    city                - e.g. "Melbourne"
    country             - e.g. "Australia"
    timezone            - IANA timezone e.g. "Australia/Melbourne"
    session_type        - QUALIFYING | SPRINT | SPRINT_1 | SPRINT_2 | FEATURE
    driver_number       - car number e.g. 7
    first_name          - e.g. "Dino"
    last_name           - e.g. "Beganovic"
    nationality         - e.g. "Swedish"
    team                - e.g. "DAMS Lucas Oil"
    grid_position       - starting grid (blank for qualifying)
    finish_position     - final position (blank for DNF/DNS/DSQ)
    status              - FINISHED | DNF | DNS | DSQ
    points              - points scored (0 if none)
    has_fastest_lap     - true/false
    fastest_lap_time    - e.g. "1:31.730" (blank if not fastest lap)

See seeds/template.csv for a reference example with 3 sample rows.
"""

import csv
import sys

sys.path.insert(0, ".")

from app.database import Base, SessionLocal, engine
from app.models.f2 import (
    Driver,
    DriverSeasonEntry,
    Result,
    ResultStatus,
    Round,
    Season,
    Session,
    SessionStatus,
    SessionType,
    Team,
)


def get_or_create_season(db, year: int) -> Season:
    obj = db.query(Season).filter(Season.year == year).first()
    if not obj:
        obj = Season(year=year)
        db.add(obj)
        db.flush()
    return obj


def get_or_create_round(db, season: Season, row: dict) -> Round:
    round_number = int(row["round_number"])
    obj = (
        db.query(Round)
        .filter(Round.season_id == season.id, Round.round_number == round_number)
        .first()
    )
    if not obj:
        obj = Round(
            season_id=season.id,
            round_number=round_number,
            name=row["round_name"],
            circuit_name=row["circuit_name"],
            city=row["city"],
            country=row["country"],
            timezone=row["timezone"],
        )
        db.add(obj)
        db.flush()
    return obj


def get_or_create_session(db, round_obj: Round, session_type: SessionType) -> Session:
    obj = (
        db.query(Session)
        .filter(Session.round_id == round_obj.id, Session.type == session_type)
        .first()
    )
    if not obj:
        from datetime import datetime

        obj = Session(
            round_id=round_obj.id,
            type=session_type,
            scheduled_at_utc=datetime(2020, 1, 1),  # placeholder for historical
            status=SessionStatus.COMPLETED,
            is_reversed_grid=(
                session_type in (SessionType.SPRINT, SessionType.SPRINT_1)
            ),
        )
        db.add(obj)
        db.flush()
    return obj


def get_or_create_driver(db, row: dict) -> Driver:
    first_name = row["first_name"].strip()
    last_name = row["last_name"].strip()
    obj = (
        db.query(Driver)
        .filter(Driver.first_name == first_name, Driver.last_name == last_name)
        .first()
    )
    if not obj:
        obj = Driver(
            first_name=first_name,
            last_name=last_name,
            nationality=row["nationality"].strip(),
            number=int(row["driver_number"]),
        )
        db.add(obj)
        db.flush()
    return obj


def get_or_create_team(db, name: str) -> Team:
    name = name.strip()
    obj = db.query(Team).filter(Team.name == name).first()
    if not obj:
        obj = Team(name=name, nationality="Unknown")
        db.add(obj)
        db.flush()
    return obj


def ensure_driver_season_entry(db, driver: Driver, team: Team, season: Season) -> None:
    existing = (
        db.query(DriverSeasonEntry)
        .filter(
            DriverSeasonEntry.driver_id == driver.id,
            DriverSeasonEntry.season_id == season.id,
        )
        .first()
    )
    if not existing:
        entry = DriverSeasonEntry(
            driver_id=driver.id,
            team_id=team.id,
            season_id=season.id,
        )
        db.add(entry)


def parse_status(value: str) -> ResultStatus:
    value = value.strip().upper()
    mapping = {
        "FINISHED": ResultStatus.FINISHED,
        "DNF": ResultStatus.DNF,
        "DNS": ResultStatus.DNS,
        "DSQ": ResultStatus.DSQ,
        "CLASSIFIED": ResultStatus.CLASSIFIED,
    }
    return mapping.get(value, ResultStatus.FINISHED)


def parse_bool(value: str) -> bool:
    return value.strip().lower() in ("true", "1", "yes")


def parse_optional_int(value: str) -> int | None:
    value = value.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def import_csv(filepath: str) -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        with open(filepath, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            print("CSV is empty.")
            return

        print(f"Read {len(rows)} rows from {filepath}")

        # Track what sessions we've already checked for existing results
        checked_sessions: set[int] = set()
        skipped_sessions: set[str] = set()
        inserted = 0

        for row in rows:
            season_year = int(row["season_year"])
            session_type = SessionType(row["session_type"].strip())

            season = get_or_create_season(db, season_year)
            round_obj = get_or_create_round(db, season, row)
            session = get_or_create_session(db, round_obj, session_type)

            # Check if this session already has results (only check once per session)
            session_key = f"{season_year}_R{row['round_number']}_{session_type.value}"
            if session.id not in checked_sessions:
                checked_sessions.add(session.id)
                existing = (
                    db.query(Result).filter(Result.session_id == session.id).first()
                )
                if existing:
                    skipped_sessions.add(session_key)

            if session_key in skipped_sessions:
                continue

            driver = get_or_create_driver(db, row)
            team = get_or_create_team(db, row["team"])
            ensure_driver_season_entry(db, driver, team, season)

            result = Result(
                session_id=session.id,
                driver_id=driver.id,
                team_id=team.id,
                grid_position=parse_optional_int(row["grid_position"]),
                finish_position=parse_optional_int(row["finish_position"]),
                status=parse_status(row["status"]),
                points=int(row["points"]) if row["points"].strip() else 0,
                has_fastest_lap=parse_bool(row["has_fastest_lap"]),
                fastest_lap_time=row["fastest_lap_time"].strip() or None,
            )
            db.add(result)
            inserted += 1

        db.commit()

        print(f"\nInserted {inserted} results.")
        if skipped_sessions:
            print(f"Skipped {len(skipped_sessions)} sessions (already had results):")
            for s in sorted(skipped_sessions):
                print(f"  - {s}")
        print("Done!")

    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_csv.py <csv_file>")
        print("Example: python scripts/import_csv.py seeds/2024_results.csv")
        sys.exit(1)

    import_csv(sys.argv[1])
