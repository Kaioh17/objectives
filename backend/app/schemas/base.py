from datetime import datetime

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    """Base for all schemas; allows validating from ORM objects."""

    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(APIModel):
    created_at: datetime
    updated_at: datetime


class Message(APIModel):
    message: str


class ErrorResponse(APIModel):
    detail: str
