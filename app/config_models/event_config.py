from pydantic import BaseModel


class EventsConfig(BaseModel):
    cleanup_sec: int