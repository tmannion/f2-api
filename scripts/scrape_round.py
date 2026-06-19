"""
Scrape F2 round results from Wikipedia and seed the local database.

Usage:
    python scripts/scrape_round.py "2026_Melbourne_Formula_2_round"

This script:
1. Fetches qualifying, sprint race, and feature race data from Wikipedia's API
2. Parses the wikitext tables into structured result data
3. Upserts the data into the local SQLite database

Data source: Wikipedia (via MediaWiki API)
"""

import re
import sys
from datetime import datetime

import requests
from sqlalchemy.orm import Session as DBSession

# Add project root to path so we can import app modules
sys.path.insert(0, ".")

from app.database import SessionLocal, engine, Base
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

# --- Wikipedia API ---

WIKI_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "F2-API-Scraper/0.1 (https://github.com; educational project)"}


def fetch_section_wikitext(page: str, section: int) -> str:
    """Fetch a specific section's wikitext from Wikipedia."""
    params = {
        "action": "parse",
        "page": page,
        "prop": "wikitext",
        "format": "json",
        "section": section,
    }
    resp = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data["parse"]["wikitext"]["*"]


def fetch_sections(page: str) -> list[dict]:
    """Fetch the section list for a Wikipedia page."""
    params = {
        "action": "parse",
        "page": page,
        "prop": "sections",
        "format": "json",
    }
    resp = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data["parse"]["sections"]


# --- Wikitext Parsing ---

# Regex patterns for extracting data from wikitext table rows
NATIONALITY_MAP = {
    "SWE": "Swedish",
    "NOR": "Norwegian",
    "IRL": "Irish",
    "IRE": "Irish",
    "MEX": "Mexican",
    "BUL": "Bulgarian",
    "BRA": "Brazilian",
    "IND": "Indian",
    "GER": "German",
    "PAR": "Paraguayan",
    "THA": "Thai",
    "NLD": "Dutch",
    "NED": "Dutch",
    "POL": "Polish",
    "JPN": "Japanese",
    "USA": "American",
    "COL": "Colombian",
    "GBR": "British",
    "ESP": "Spanish",
    "ARG": "Argentine",
    "ITA": "Italian",
    "FRA": "French",
    "AUS": "Australian",
    "CAN": "Canadian",
    "FIN": "Finnish",
    "DEN": "Danish",
    "CHN": "Chinese",
    "ISR": "Israeli",
    "RSA": "South African",
    "NZL": "New Zealander",
}


def parse_driver_name(text: str) -> str:
    """Extract driver name from wikitext like [[Joshua Dürksen]] or [[John Bennett (racing driver)|John Bennett]]."""
    match = re.search(r"\[\[([^\]|]+?)(?:\|([^\]]+))?\]\]", text)
    if match:
        return match.group(2) if match.group(2) else match.group(1)
    return text.strip()


def parse_nationality(text: str) -> str:
    """Extract nationality code from flagicon template."""
    match = re.search(r"\{\{[Ff]lag\s*icon\|(\w+)\}\}", text)
    if match:
        code = match.group(1).upper()
        return NATIONALITY_MAP.get(code, code)
    return "Unknown"


def parse_team_name(text: str) -> str:
    """Extract team name from wikitext link like [[Invicta Racing]] or [[DAMS|DAMS Lucas Oil]]."""
    # Handle multiple links (e.g. [[Hitech Grand Prix|Hitech]] [[Toyota Gazoo Racing|TGR]])
    links = re.findall(r"\[\[([^\]|]+?)(?:\|([^\]]+))?\]\]", text)
    if links:
        # Use the display text (group 2) if available, otherwise the link target
        parts = []
        for link_target, display in links:
            parts.append(display if display else link_target)
        return " ".join(parts)
    return text.strip("' ")


def parse_race_table(wikitext: str) -> list[dict]:
    """Parse a race results table from wikitext into structured data."""
    results = []
    lines = wikitext.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Look for position indicator (start of a result row)
        # Format: !1 or !DNF or !DSQ etc.
        pos_match = re.match(r"^!(\d+|DNF|DNS|DSQ|—)$", line)
        if pos_match:
            pos_text = pos_match.group(1)
            row_lines = []

            # Collect all lines until the next |- or |}
            i += 1
            while (
                i < len(lines)
                and not lines[i].strip().startswith("|-")
                and not lines[i].strip().startswith("|}")
            ):
                row_lines.append(lines[i])
                i += 1

            # Parse the collected row
            result = parse_result_row(pos_text, row_lines)
            if result:
                results.append(result)
        else:
            i += 1

    return results


def parse_result_row(position_text: str, row_lines: list[str]) -> dict | None:
    """Parse a single result row from collected lines."""
    # Filter to actual data cells (lines starting with | but not |-)
    cells = []
    for line in row_lines:
        stripped = line.strip()
        if (
            stripped.startswith("|")
            and not stripped.startswith("|-")
            and not stripped.startswith("|}")
        ):
            # Remove leading | and possible align attributes
            cell_content = re.sub(r"^\|\s*(?:align=\"\w+\"\s*\|)?", "", stripped)
            cells.append(cell_content.strip())

    if len(cells) < 4:
        return None

    # Determine position and status
    if position_text == "DNF":
        status = ResultStatus.DNF
        finish_position = None
    elif position_text == "DNS":
        status = ResultStatus.DNS
        finish_position = None
    elif position_text == "DSQ":
        status = ResultStatus.DSQ
        finish_position = None
    elif position_text == "—":
        return None  # Skip non-classified entries without position
    else:
        status = ResultStatus.FINISHED
        finish_position = int(position_text)

    # Extract car number
    car_number = None
    number_match = re.search(r"(\d+)", cells[0])
    if number_match:
        car_number = int(number_match.group(1))

    # Extract driver info (cell index 1 typically has flag + driver name)
    driver_cell = cells[1]
    driver_name = parse_driver_name(driver_cell)
    nationality = parse_nationality(driver_cell)

    # Extract team (cell index 2)
    team_cell = cells[2]
    team_name = parse_team_name(team_cell)

    # Extract points if present (last meaningful cell)
    points = 0
    if len(cells) >= 5:
        points_cell = cells[-1]
        # Handle points like "'''10'''" or "'''15+1'''" (fastest lap bonus)
        points_text = re.sub(r"'{2,3}", "", points_cell).strip()
        points_match = re.match(r"(\d+)(?:\+(\d+))?", points_text)
        if points_match:
            points = int(points_match.group(1))
            if points_match.group(2):
                points += int(points_match.group(2))

    # Extract grid position if available
    grid_position = None
    # For race tables, grid is typically the second-to-last cell
    if len(cells) >= 6:
        grid_cell = cells[-2]
        grid_match = re.search(r"(\d+)", grid_cell)
        if grid_match:
            grid_position = int(grid_match.group(1))

    # Split driver name into first/last
    name_parts = driver_name.split(" ", 1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""

    return {
        "finish_position": finish_position,
        "status": status,
        "car_number": car_number,
        "first_name": first_name,
        "last_name": last_name,
        "nationality": nationality,
        "team_name": team_name,
        "grid_position": grid_position,
        "points": points,
    }


def parse_fastest_lap(wikitext: str) -> tuple[str | None, str | None]:
    """Extract fastest lap driver and time from wikitext."""
    match = re.search(
        r"Fastest lap:.*?\[\[([^\]|]+?)(?:\|[^\]]+)?\]\].*?\((\d+:\d+\.\d+)",
        wikitext,
    )
    if match:
        driver_name = match.group(1)
        lap_time = match.group(2)
        return driver_name, lap_time
    return None, None


# --- Database Operations ---


def get_or_create_season(db: DBSession, year: int) -> Season:
    """Get existing season or create new one."""
    season = db.query(Season).filter(Season.year == year).first()
    if not season:
        season = Season(year=year)
        db.add(season)
        db.commit()
        db.refresh(season)
    return season


def get_or_create_team(db: DBSession, name: str) -> Team:
    """Get existing team or create new one."""
    team = db.query(Team).filter(Team.name == name).first()
    if not team:
        team = Team(name=name, nationality="Unknown")
        db.add(team)
        db.commit()
        db.refresh(team)
    return team


def get_or_create_driver(
    db: DBSession, first_name: str, last_name: str, nationality: str, number: int
) -> Driver:
    """Get existing driver or create new one."""
    driver = (
        db.query(Driver)
        .filter(Driver.first_name == first_name, Driver.last_name == last_name)
        .first()
    )
    if not driver:
        driver = Driver(
            first_name=first_name,
            last_name=last_name,
            nationality=nationality,
            number=number,
        )
        db.add(driver)
        db.commit()
        db.refresh(driver)
    return driver


def get_or_create_round(
    db: DBSession,
    season: Season,
    round_number: int,
    name: str,
    circuit_name: str,
    city: str,
    country: str,
    timezone: str,
) -> Round:
    """Get existing round or create new one."""
    round_obj = (
        db.query(Round)
        .filter(Round.season_id == season.id, Round.round_number == round_number)
        .first()
    )
    if not round_obj:
        round_obj = Round(
            season_id=season.id,
            round_number=round_number,
            name=name,
            circuit_name=circuit_name,
            city=city,
            country=country,
            timezone=timezone,
        )
        db.add(round_obj)
        db.commit()
        db.refresh(round_obj)
    return round_obj


def get_or_create_session(
    db: DBSession,
    round_obj: Round,
    session_type: SessionType,
    scheduled_at_utc: datetime,
    is_reversed_grid: bool = False,
) -> Session:
    """Get existing session or create new one."""
    session = (
        db.query(Session)
        .filter(Session.round_id == round_obj.id, Session.type == session_type)
        .first()
    )
    if not session:
        session = Session(
            round_id=round_obj.id,
            type=session_type,
            scheduled_at_utc=scheduled_at_utc,
            status=SessionStatus.COMPLETED,
            is_reversed_grid=is_reversed_grid,
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


def seed_results(
    db: DBSession,
    session: Session,
    season: Season,
    results_data: list[dict],
    fastest_lap_driver: str | None,
    fastest_lap_time: str | None,
) -> None:
    """Insert results for a session, skipping if results already exist."""
    existing = db.query(Result).filter(Result.session_id == session.id).first()
    if existing:
        print(f"  Results already exist for session {session.type.value}, skipping.")
        return

    for row in results_data:
        driver = get_or_create_driver(
            db,
            row["first_name"],
            row["last_name"],
            row["nationality"],
            row["car_number"] or 0,
        )
        team = get_or_create_team(db, row["team_name"])

        # Check if this driver has a fastest lap
        has_fl = False
        fl_time = None
        if fastest_lap_driver:
            full_name = f"{row['first_name']} {row['last_name']}"
            if full_name in fastest_lap_driver or fastest_lap_driver in full_name:
                has_fl = True
                fl_time = fastest_lap_time

        result = Result(
            session_id=session.id,
            driver_id=driver.id,
            team_id=team.id,
            grid_position=row["grid_position"],
            finish_position=row["finish_position"],
            status=row["status"],
            points=row["points"],
            has_fastest_lap=has_fl,
            fastest_lap_time=fl_time,
        )
        db.add(result)

        # Ensure driver-season entry exists
        entry = (
            db.query(DriverSeasonEntry)
            .filter(
                DriverSeasonEntry.driver_id == driver.id,
                DriverSeasonEntry.season_id == season.id,
            )
            .first()
        )
        if not entry:
            entry = DriverSeasonEntry(
                driver_id=driver.id,
                team_id=team.id,
                season_id=season.id,
            )
            db.add(entry)

    db.commit()
    print(f"  Inserted {len(results_data)} results for {session.type.value}.")


# --- Main ---


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/scrape_round.py <wikipedia_page_name>")
        print(
            'Example: python scripts/scrape_round.py "2026_Melbourne_Formula_2_round"'
        )
        sys.exit(1)

    page = sys.argv[1]
    print(f"Fetching data for: {page}")

    # Fetch section list to find qualifying, sprint, feature
    sections = fetch_sections(page)

    section_map = {}
    for sec in sections:
        line_lower = sec["line"].lower()
        if "qualifying" in line_lower:
            section_map["qualifying"] = int(sec["index"])
        elif "sprint" in line_lower:
            section_map["sprint"] = int(sec["index"])
        elif "feature" in line_lower:
            section_map["feature"] = int(sec["index"])

    print(f"Found sections: {list(section_map.keys())}")

    # Parse metadata from page name
    # Expected format: "2026_Melbourne_Formula_2_round"
    year_match = re.match(r"(\d{4})_(\w+)_Formula_2_round", page)
    if not year_match:
        print(f"Cannot parse year/city from page name: {page}")
        sys.exit(1)

    year = int(year_match.group(1))
    city = year_match.group(2)

    # Create database tables if needed
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Create season and round
        season = get_or_create_season(db, year)
        round_obj = get_or_create_round(
            db,
            season=season,
            round_number=1,  # Australia is round 1 for 2026
            name=f"{city} Round",
            circuit_name="Albert Park Circuit",
            city=city,
            country="Australia",
            timezone="Australia/Melbourne",
        )

        # Process each session type
        session_configs = [
            (
                "qualifying",
                SessionType.QUALIFYING,
                datetime(year, 3, 6, 3, 55),
            ),  # 14:55 UTC+11
            ("sprint", SessionType.SPRINT, datetime(year, 3, 7, 3, 10)),  # 14:10 UTC+11
            (
                "feature",
                SessionType.FEATURE,
                datetime(year, 3, 8, 0, 25),
            ),  # 11:25 UTC+11
        ]

        for key, session_type, scheduled_utc in session_configs:
            if key not in section_map:
                print(f"  Section '{key}' not found, skipping.")
                continue

            print(f"\nProcessing {key}...")
            wikitext = fetch_section_wikitext(page, section_map[key])
            results_data = parse_race_table(wikitext)
            fastest_driver, fastest_time = parse_fastest_lap(wikitext)

            print(f"  Parsed {len(results_data)} results.")
            if fastest_driver:
                print(f"  Fastest lap: {fastest_driver} ({fastest_time})")

            is_reversed = session_type == SessionType.SPRINT
            session = get_or_create_session(
                db, round_obj, session_type, scheduled_utc, is_reversed_grid=is_reversed
            )
            seed_results(
                db, session, season, results_data, fastest_driver, fastest_time
            )

        print("\nDone! Database seeded with Australia round data.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
