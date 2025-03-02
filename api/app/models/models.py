from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, func
from ..database.database import Base
import datetime
from sqlalchemy.types import DateTime
class User(Base):
    __tablename__ = 'users'

    id = Column(String, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    is_admin = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    is_deleted = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    is_verified = Column(Integer, default=0)
    is_locked = Column(Integer, default=0)
    is_premium = Column(Integer, default=0)
    is_subscribed = Column(Integer, default=0)
    stripe_customer_id = Column(String, index=True, nullable=True, default=None)
    stripe_subscription_id = Column(String, index=True, nullable=True, default=None)

class Section(Base):
    __tablename__ = 'sections'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(String, ForeignKey('users.id'), index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now)
    is_deleted = Column(Integer, default=0)

class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('users.id'), index=True)
    section_id = Column(Integer, ForeignKey('sections.id'), index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    is_deleted = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    
class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('users.id'), index=True)
    category_id = Column(Integer, ForeignKey('categories.id'), index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    date = Column(Date)
    amount = Column(Float)
    is_indexed = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    is_deleted = Column(Integer, default=0)
    is_imported = Column(Integer, default=0)
    is_manual = Column(Integer, default=0)
    is_linked = Column(Integer, default=0)

class Budget(Base):
    __tablename__ = 'budgets'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('users.id'), index=True)
    category_id = Column(Integer, ForeignKey('categories.id'), index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    amount = Column(Float)
    version = Column(Integer, default=1)
    valid_from = Column(DateTime, default=datetime.datetime.now)
    valid_to = Column(DateTime, nullable=True)
    active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    is_deleted = Column(Integer, default=0)

class CategoryCorrections(Base):
    __tablename__ = 'category_corrections'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey('users.id'), index=True)
    transaction_id = Column(Integer, ForeignKey('transactions.id'), index=True)
    old_category_id = Column(Integer, ForeignKey('categories.id'), index=True)
    new_category_id = Column(Integer, ForeignKey('categories.id'), index=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)