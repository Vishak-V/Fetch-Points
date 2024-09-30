from pydantic import BaseModel, EmailStr
from datetime import datetime


#Schemas to restrict the data types of the request body
class Transaction(BaseModel):
    payer: str
    points: int
    timestamp: datetime

class SpendRequest(BaseModel):
    points: int

