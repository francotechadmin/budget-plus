from pydantic import BaseModel


class DescriptionRequest(BaseModel):
    description: str


class UpdateTransactionRequest(BaseModel):
    transaction_id: int
    category: str
