from pydantic import BaseModel


class Challenge(BaseModel):
    challenger: str
    challenged: str
    challenge_id: str  # this should be changed for game_name
