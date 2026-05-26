from dataclasses import dataclass


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    display_name: str
