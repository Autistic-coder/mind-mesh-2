from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=2, max_length=80)
    password: str = Field(min_length=10, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: EmailStr
    display_name: str
    created_at: datetime


class MachineInput(BaseModel):
    type: Literal["L", "M", "H"] = Field(alias="Type")
    air_temperature: float = Field(ge=290, le=310, alias="Air temperature [K]")
    process_temperature: float = Field(ge=300, le=320, alias="Process temperature [K]")
    rotational_speed: float = Field(ge=1100, le=3000, alias="Rotational speed [rpm]")
    torque: float = Field(ge=0, le=80, alias="Torque [Nm]")
    tool_wear: float = Field(ge=0, le=300, alias="Tool wear [min]")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("type", mode="before")
    @classmethod
    def normalize_type(cls, value: str) -> str:
        return value.strip().upper() if isinstance(value, str) else value

    def feature_dict(self) -> dict[str, float | str]:
        return self.model_dump(by_alias=True)


class PredictionResponse(BaseModel):
    id: str
    probability: float
    predicted_failure: bool
    result: str
    risk_level: str
    recommendation: str
    model_version: str
    created_at: datetime
    inputs: dict


class ProfileUpdate(BaseModel):
    display_name: str = Field(min_length=2, max_length=80)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    share_prediction: bool = False
    prediction_id: str | None = None
