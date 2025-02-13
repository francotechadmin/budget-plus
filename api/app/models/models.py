from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from ..database.database import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    is_admin = Column(Integer, default=0)
    created_at = Column(Date)
    updated_at = Column(Date)
    is_deleted = Column(Integer, default=0)
    is_active = Column(Integer, default=1)
    is_verified = Column(Integer, default=0)
    is_locked = Column(Integer, default=0)
    is_premium = Column(Integer, default=0)
    is_subscribed = Column(Integer, default=0)
    stripe_customer_id = Column(String, index=True)
    stripe_subscription_id = Column(String, index=True)

class Section(Base):
    __tablename__ = 'sections'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    created_at = Column(Date)
    updated_at = Column(Date)
    is_deleted = Column(Integer, default=0)

class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    section_id = Column(Integer, ForeignKey('sections.id'), index=True)
    created_at = Column(Date)
    updated_at = Column(Date)
    is_deleted = Column(Integer, default=0)
    
class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    category_id = Column(Integer, ForeignKey('categories.id'), index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    date = Column(Date)
    amount = Column(Float)
    is_indexed = Column(Integer, default=0)
    created_at = Column(Date)
    updated_at = Column(Date)
    is_deleted = Column(Integer, default=0)







# -- Users table (optional local profile)
# CREATE TABLE users (
#     id VARCHAR(50) PRIMARY KEY,  -- matches Auth0 user id
#     email VARCHAR(255),
#     name VARCHAR(255),
#     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
# );

# -- Sections table (user-specific; remove user_id if global)
# CREATE TABLE sections (
#     id SERIAL PRIMARY KEY,
#     user_id VARCHAR(50),  -- remove if sections are global
#     name VARCHAR(100) NOT NULL,
#     description TEXT,
#     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#     FOREIGN KEY (user_id) REFERENCES users(id)
# );

# -- Categories table (user-specific; remove user_id if global)
# CREATE TABLE categories (
#     id SERIAL PRIMARY KEY,
#     user_id VARCHAR(50),  -- remove if categories are global
#     section_id INT NOT NULL,
#     name VARCHAR(100) NOT NULL,
#     description TEXT,
#     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#     FOREIGN KEY (user_id) REFERENCES users(id),
#     FOREIGN KEY (section_id) REFERENCES sections(id)
# );

# -- Transactions table
# CREATE TABLE transactions (
#     id SERIAL PRIMARY KEY,
#     user_id VARCHAR(50) NOT NULL,  -- should match Auth0's id
#     category_id INT NOT NULL,
#     transaction_date TIMESTAMP NOT NULL,
#     amount DECIMAL(10,2) NOT NULL,
#     description TEXT,
#     type VARCHAR(10),  -- e.g., 'credit' or 'debit'
#     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
#     FOREIGN KEY (user_id) REFERENCES users(id),
#     FOREIGN KEY (category_id) REFERENCES categories(id)
# );

