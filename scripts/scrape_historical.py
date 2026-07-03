"""
Bulk scrape historical F2 data from Wikipedia for seasons 2020-2025.

Usage:
    python scripts/scrape_historical.py                    # All seasons 2020-2025
    python scripts/scrape_historical.py --year 2024       # Single season
    python scripts/scrape_historical.py --year 2024 --round "2024_Melbourne_Formula_2_round"

Handles format differences across eras:
- 2020: QUALIFYING + FEATURE + SPRINT (2-race format)
- 2021: QUALIFYING + SPRINT_1 + SPRINT_2 + FEATURE (3-race format)
- 2022-2025: QUALIFYING + SPRINT + FEATURE (current format)
"""

import argparse
import re
import sys
import time
from datetime import datetime

import requests
from sqlalchemy.orm import Session as DBSession

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

WIKI_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "F2-API-Scraper/0.1 (https://github.com; educational project)"}
REQUEST_DELAY = 1.0


# --- Wikipedia API ---


def wiki_request(params: dict) -> dict:
    """Make a request to the Wikipedia API with rate limiting."""
    time.sleep(REQUEST_DELAY)
    resp = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()


def fetch_round_pages(year: int) -> list[str]:
    """Get all F2 round page names for a given season."""
    page = f"{year}_Formula_2_Championship"
    data = wiki_request(
        {"action": "parse", "page": page, "prop": "links", "format": "json"}
    )
    links = data["parse"]["links"]
    rounds = [
        link["*"]
        for link in links
        if "Formula 2 round" in link.get("*", "") and str(year) in link.get("*", "")
    ]
    return sorted(rounds)


def fetch_sections(page: str) -> list[dict]:
    """Fetch the section list for a Wikipedia page."""
    data = wiki_request(
        {"action": "parse", "page": page, "prop": "sections", "format": "json"}
    )
    return data["parse"]["sections"]


def fetch_section_wikitext(page: str, section: int) -> str:
    """Fetch a specific section's wikitext from Wikipedia."""
    data = wiki_request(
        {
            "action": "parse",
            "page": page,
            "prop": "wikitext",
            "format": "json",
            "section": section,
        }
    )
    return data["parse"]["wikitext"]["*"]


# --- Wikitext Parsing ---

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
    "RUS": "Russian",
    "EST": "Estonian",
    "IDN": "Indonesian",
    "INA": "Indonesian",
    "TUR": "Turkish",
    "SUI": "Swiss",
    "MON": "Monégasque",
    "CZE": "Czech",
    "UAE": "Emirati",
    "POR": "Portuguese",
    "BEL": "Belgian",
    "HUN": "Hungarian",
    "AUT": "Austrian",
    "KOR": "South Korean",
    "SAU": "Saudi",
    "URU": "Uruguayan",
    "VEN": "Venezuelan",
}


def parse_driver_name(text: str) -> str:
    """Extract driver name from wikitext link."""
    match = re.search(r"\[\[([^\]|]+?)(?:\|([^\]]+))?\]\]", text)
    if match:
        return match.group(2) if match.group(2) else match.group(1)
    return text.strip()


def parse_nationality(text: str) -> str:
    """Extract nationality from flagicon template."""
    match = re.search(r"\{\{[Ff]lag\s*icon\|(\w+)\}\}", text)
    if match:
        code = match.group(1).upper()
        return NATIONALITY_MAP.get(code, code)
    return "Unknown"


def parse_team_name(text: str) -> str:
    """Extract team name from wikitext link."""
    links = re.findall(r"\[\[([^\]|]+?)(?:\|([^\]]+))?\]\]", text)
    if links:
        parts = []
        for _, display in links:
            parts.append(display if display else _)
        return " ".join(parts)
    return text.strip("' ")


def parse_race_table(wikitext: str) -> list[dict]:
    """Parse a race results table from wikitext into structured data."""
    results = []
    lines = wikitext.split("\n")

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Match position: "!1", "! 1", "!DNF", '! scope="row"| 1', etc.
        pos_match = re.match(
            r'^!\s*(?:scope="row"\s*\|\s*)?(\d+|DNF|DNS|DSQ|NC|Ret|WD|EX|—|\'\'\'DNF\'\'\'|\'\'\'Ret\'\'\')$',
            line,
            re.IGNORECASE,
        )
        if pos_match:
            pos_text = pos_match.group(1).strip("'")
            row_lines = []

            i += 1
            while i < len(lines):
                stripped = lines[i].strip()
                if stripped.startswith("|-") or stripped.startswith("|}"):
                    break
                row_lines.append(lines[i])
                i += 1

            result = parse_result_row(pos_text, row_lines)
            if result:
                results.append(result)
        else:
            i += 1

    return results


def parse_result_row(position_text: str, row_lines: list[str]) -> dict | None:
    """Parse a single result row from collected lines."""
    cells = []
    for line in row_lines:
        stripped = line.strip()
        if (
            stripped.startswith("|")
            and not stripped.startswith("|-")
            and not stripped.startswith("|}")
        ):
            # Remove leading pipe, then handle "align/nowrap/scope" attributes
            # Format variants: "| value", '| align="center" |value',
            # '| align="center"| value', '| scope="row"| value'
            cell_content = re.sub(
                r"^\|\s*(?:(?:align|nowrap|scope)=\"[^\"]*\"\s*\|?\s*)*",
                "",
                stripped,
            )
            cells.append(cell_content.strip())

    if len(cells) < 4:
        return None

    # Determine status
    pos_upper = position_text.upper()
    if pos_upper in ("DNF", "RET"):
        status = ResultStatus.DNF
        finish_position = None
    elif pos_upper == "DNS":
        status = ResultStatus.DNS
        finish_position = None
    elif pos_upper in ("DSQ", "EX"):
        status = ResultStatus.DSQ
        finish_position = None
    elif pos_upper in ("NC", "—", "WD"):
        return None
    else:
        try:
            finish_position = int(position_text)
            status = ResultStatus.FINISHED
        except ValueError:
            return None

    # Extract car number (first cell)
    car_number = None
    number_match = re.search(r"(\d+)", cells[0])
    if number_match:
        car_number = int(number_match.group(1))

    # Extract driver info (second cell)
    driver_cell = cells[1]
    driver_name = parse_driver_name(driver_cell)
    nationality = parse_nationality(driver_cell)

    # Extract team (third cell)
    team_cell = cells[2]
    team_name = parse_team_name(team_cell)

    # Extract points (last cell)
    points = 0
    if len(cells) >= 5:
        points_cell = cells[-1]
        points_text = re.sub(r"'{2,3}", "", points_cell).strip()
        # Remove ref tags
        points_text = re.sub(r"\{\{[Rr]ef\|[^}]*\}\}", "", points_text).strip()
        points_match = re.match(r"(\d+)(?:\+(\d+))?", points_text)
        if points_match:
            points = int(points_match.group(1))
            if points_match.group(2):
                points += int(points_match.group(2))

    # Extract grid position (second-to-last for race tables with points)
    grid_position = None
    if len(cells) >= 6:
        grid_cell = cells[-2]
        grid_match = re.search(r"(\d+)", grid_cell)
        if grid_match:
            grid_position = int(grid_match.group(1))

    # Split driver name
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
        r"[Ff]astest lap:.*?\[\[([^\]|]+?)(?:\|[^\]]+)?\]\].*?\((\d+:\d+\.\d+)",
        wikitext,
    )
    if match:
        return match.group(1), match.group(2)
    return None, None


def identify_sessions(sections: list[dict]) -> list[tuple[str, SessionType, int]]:
    """Identify race session sections and map to SessionType.

    If a session type appears multiple times (e.g. Yas Island 2022 has sections
    for pre-round standings AND classification), use the LAST occurrence which
    is the actual results section.
    """
    found: dict[str, tuple[str, SessionType, int]] = {}
    for sec in sections:
        line = sec["line"].lower().strip()
        index = int(sec["index"])

        if "qualifying" in line:
            found["qualifying"] = ("qualifying", SessionType.QUALIFYING, index)
        elif "sprint race 1" in line or "sprint 1" in line:
            found["sprint_1"] = ("sprint_1", SessionType.SPRINT_1, index)
        elif "sprint race 2" in line or "sprint 2" in line:
            found["sprint_2"] = ("sprint_2", SessionType.SPRINT_2, index)
        elif "sprint" in line:
            found["sprint"] = ("sprint", SessionType.SPRINT, index)
        elif "feature" in line:
            found["feature"] = ("feature", SessionType.FEATURE, index)

    return list(found.values())


# --- Database Operations ---


def get_or_create_season(db: DBSession, year: int) -> Season:
    obj = db.query(Season).filter(Season.year == year).first()
    if not obj:
        obj = Season(year=year)
        db.add(obj)
        db.commit()
        db.refresh(obj)
    return obj


def get_or_create_team(db: DBSession, name: str) -> Team:
    obj = db.query(Team).filter(Team.name == name).first()
    if not obj:
        obj = Team(name=name, nationality="Unknown")
        db.add(obj)
        db.commit()
        db.refresh(obj)
    return obj


def get_or_create_driver(
    db: DBSession, first_name: str, last_name: str, nationality: str, number: int
) -> Driver:
    obj = (
        db.query(Driver)
        .filter(Driver.first_name == first_name, Driver.last_name == last_name)
        .first()
    )
    if not obj:
        obj = Driver(
            first_name=first_name,
            last_name=last_name,
            nationality=nationality,
            number=number,
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
    return obj


def get_or_create_round(
    db: DBSession, season: Season, round_number: int, name: str, city: str
) -> Round:
    obj = (
        db.query(Round)
        .filter(Round.season_id == season.id, Round.round_number == round_number)
        .first()
    )
    if not obj:
        obj = Round(
            season_id=season.id,
            round_number=round_number,
            name=name,
            circuit_name=name,
            city=city,
            country="Unknown",
            timezone="UTC",
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
    return obj


def get_or_create_session(
    db: DBSession, round_obj: Round, session_type: SessionType
) -> Session:
    obj = (
        db.query(Session)
        .filter(Session.round_id == round_obj.id, Session.type == session_type)
        .first()
    )
    if not obj:
        obj = Session(
            round_id=round_obj.id,
            type=session_type,
            scheduled_at_utc=datetime(2020, 1, 1),
            status=SessionStatus.COMPLETED,
            is_reversed_grid=(
                session_type in (SessionType.SPRINT, SessionType.SPRINT_1)
            ),
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
    return obj


def seed_results(
    db: DBSession,
    session: Session,
    season: Season,
    results_data: list[dict],
    fastest_lap_driver: str | None,
    fastest_lap_time: str | None,
) -> int:
    """Insert results for a session. Returns count or 0 if skipped."""
    existing = db.query(Result).filter(Result.session_id == session.id).first()
    if existing:
        return 0

    for row in results_data:
        driver = get_or_create_driver(
            db,
            row["first_name"],
            row["last_name"],
            row["nationality"],
            row["car_number"] or 0,
        )
        team = get_or_create_team(db, row["team_name"])

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
                driver_id=driver.id, team_id=team.id, season_id=season.id
            )
            db.add(entry)

    db.commit()
    return len(results_data)


# --- Main Logic ---


def scrape_round(
    db: DBSession, season: Season, round_number: int, page: str, report: list
) -> None:
    """Scrape a single round from Wikipedia."""
    city_match = re.match(
        r"\d{4}_(?:2nd_)?(.+?)_(?:FIA_)?Formula_2_round", page.replace(" ", "_")
    )
    city = city_match.group(1).replace("_", " ") if city_match else "Unknown"
    round_name = f"{city} Round"

    print(f"  Round {round_number}: {city}")

    try:
        sections = fetch_sections(page)
    except Exception as e:
        print(f"    ERROR fetching sections: {e}")
        report.append(
            {
                "season": season.year,
                "round": round_number,
                "city": city,
                "issue": f"fetch error: {e}",
            }
        )
        return

    if not sections:
        print("    WARNING: Empty page (likely a redirect), skipping.")
        report.append(
            {
                "season": season.year,
                "round": round_number,
                "city": city,
                "issue": "empty page (redirect)",
            }
        )
        return

    session_info = identify_sessions(sections)
    if not session_info:
        print("    WARNING: No race sessions found, skipping.")
        report.append(
            {
                "season": season.year,
                "round": round_number,
                "city": city,
                "issue": "no sessions identified",
            }
        )
        return

    round_obj = get_or_create_round(db, season, round_number, round_name, city)

    for name, session_type, section_index in session_info:
        try:
            wikitext = fetch_section_wikitext(page, section_index)
        except Exception as e:
            print(f"    ERROR fetching {name}: {e}")
            report.append(
                {
                    "season": season.year,
                    "round": round_number,
                    "city": city,
                    "session": session_type.value,
                    "issue": f"fetch error: {e}",
                }
            )
            continue

        results_data = parse_race_table(wikitext)
        if not results_data:
            print(f"    WARNING: No results parsed for {name}")
            report.append(
                {
                    "season": season.year,
                    "round": round_number,
                    "city": city,
                    "session": session_type.value,
                    "issue": "no results parsed",
                }
            )
            continue

        if len(results_data) < 18:
            report.append(
                {
                    "season": season.year,
                    "round": round_number,
                    "city": city,
                    "session": session_type.value,
                    "issue": f"incomplete: {len(results_data)} results (expected 20-22)",
                }
            )

        fastest_driver, fastest_time = parse_fastest_lap(wikitext)
        session = get_or_create_session(db, round_obj, session_type)
        count = seed_results(
            db, session, season, results_data, fastest_driver, fastest_time
        )

        if count > 0:
            print(f"    {session_type.value}: {count} results")
        else:
            print(f"    {session_type.value}: already exists, skipped")


def scrape_season(db: DBSession, year: int, report: list) -> None:
    """Scrape all rounds for a given season."""
    print(f"\n{'=' * 60}")
    print(f"Season {year}")
    print(f"{'=' * 60}")

    season = get_or_create_season(db, year)

    try:
        round_pages = fetch_round_pages(year)
    except Exception as e:
        print(f"  ERROR fetching round list: {e}")
        return

    print(f"  Found {len(round_pages)} rounds\n")

    for i, page in enumerate(round_pages, start=1):
        scrape_round(db, season, i, page, report)


def print_report(report: list) -> None:
    """Print a summary of missing/incomplete data."""
    if not report:
        print("\n  No issues found — all data imported successfully!")
        return

    print(f"\n{'=' * 60}")
    print("MISSING/INCOMPLETE DATA REPORT")
    print(f"{'=' * 60}")
    print(f"\n  {len(report)} issue(s) found:\n")

    for item in report:
        season = item.get("season", "?")
        rd = item.get("round", "?")
        city = item.get("city", "?")
        session = item.get("session", "ALL")
        issue = item.get("issue", "unknown")
        print(f"  [{season} R{rd} {city}] {session}: {issue}")

    print("\n  Use Swagger UI (POST endpoints) to manually add missing data.")
    print("  Or check the Wikipedia page formatting for these specific rounds.")


def main():
    parser = argparse.ArgumentParser(
        description="Scrape historical F2 data from Wikipedia"
    )
    parser.add_argument(
        "--year", type=int, help="Single season to scrape (default: all 2020-2025)"
    )
    parser.add_argument(
        "--round", type=str, help="Single round page to scrape (requires --year)"
    )
    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    report: list = []

    try:
        if args.year and args.round:
            season = get_or_create_season(db, args.year)
            scrape_round(db, season, 1, args.round, report)
        elif args.year:
            scrape_season(db, args.year, report)
        else:
            for year in range(2020, 2026):
                scrape_season(db, year, report)

        print("\n\nDone!")
        print_report(report)
    finally:
        db.close()


if __name__ == "__main__":
    main()
