from sqlalchemy import Column, Integer, String, Float, Date
from ..database.database import Base


class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, index=True)
    date = Column(Date)
    amount = Column(Float)
    category = Column(String)
    section = Column(String)
    is_indexed = Column(Integer, default=0)


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    section = Column(String, index=True)
    category = Column(String, index=True)
