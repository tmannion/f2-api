from pydantic import BaseModel


class StandingEntry(BaseModel):
    position: int
    driver_id: int
    driver_name: str
    team_name: str
    points: int
    wins: int
    podiums: int


class StandingsResponse(BaseModel):
    season_id: int
    season_year: int
    standings: list[StandingEntry]
