from pydantic import BaseModel
import datetime
from typing import Optional

class UserCreate(BaseModel):
    """UserCreate schema for creating a new user."""
    id: str
    email: str
    name: str
class UserRead(BaseModel):
    """UserRead schema for reading user data."""
    id: str
    email: str
    name: str
    is_admin: int = 0
    created_at: datetime.datetime
    updated_at: datetime.datetime
    is_deleted: int = 0
    is_active: int = 1
    is_verified: int = 0
    is_locked: int = 0
    is_premium: int = 0
    is_subscribed: int = 0
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None


class DescriptionRequest(BaseModel):
    """DescriptionRequest schema for updating a transaction description."""
    description: str


class NewTransactionRequest(BaseModel):
    """NewTransactionRequest schema for creating a new transaction."""
    description: str
    amount: float
    date: datetime.date
    category: Optional[str] = None

class UpdateTransactionRequest(BaseModel):
    """UpdateTransactionRequest schema for updating a transaction's category."""
    transaction_id: int
    category: str
    index_es: Optional[str] = None
