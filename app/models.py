from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from .database import Base

class App(Base):
    __tablename__ = "apps"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

class Environment(Base):
    __tablename__ = "environments"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    app_id = Column(Integer, ForeignKey("apps.id"), nullable=False)

class Variable(Base):
    __tablename__ = "variables"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, nullable=False)
    value = Column(Text, nullable=False)
    env_id = Column(Integer, ForeignKey("environments.id"), nullable=False)

class Secret(Base):
    __tablename__ = "secrets"
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, nullable=False)
    ssm_path = Column(String, nullable=False)
    env_id = Column(Integer, ForeignKey("environments.id"), nullable=False)

class TaskDefinitionTemplate(Base):
    __tablename__ = "td_templates"
    id = Column(Integer, primary_key=True, index=True)
    env_id = Column(Integer, ForeignKey("environments.id"), nullable=False)
    target_container = Column(String, nullable=False)
    base_json = Column(Text, nullable=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
