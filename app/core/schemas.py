from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class UserCreate(BaseModel):
	username: str = Field(..., min_length=3, max_length=50, description='Username')
	password: str = Field(..., min_length=4, description='User password')
	role: str = Field(..., description='Role name')

class UserResponse(BaseModel):
	id: int
	username: str
	role: str

	model_config = ConfigDict(
		from_attributes = True,
	)

class LoginRequest(BaseModel):
	username: str = Field(..., min_length=3, max_length=50, description='Username')
	password: str = Field(..., min_length=4, description='User password')

	model_config = ConfigDict(
		extra='forbid'
	)
