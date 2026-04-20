from pydantic import BaseModel, ConfigDict


class AppBaseModel(BaseModel):
    """Base model for all request schemas — rejects unknown fields."""

    model_config = ConfigDict(extra="forbid")
