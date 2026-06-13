from pydantic import BaseModel, Field


class PushSettingsUpdate(BaseModel):
    channel_app: bool = True
    channel_sms: bool = False
    quiet_hours: str | None = Field(None, pattern=r"^\d{2}:\d{2}-\d{2}:\d{2}$")
