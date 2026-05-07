from pydantic import BaseModel, Field


class UserCreate(BaseModel):
	username: str
	password: str
	role: str

class UserResponse(BaseModel):
	id: int
	username: str
	role: str

	class Config:
		from_attributes = True

class LoginRequest(BaseModel):
	username: str = Field(..., min_length=3, max_length=50, description='Username')
	password: str = Field(..., min_length=4, description='User password')
