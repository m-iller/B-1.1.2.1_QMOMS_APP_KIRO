from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: str
    username: str
    role: str

class LoginResponse(BaseModel):
    access_token: str
    user: UserResponse
