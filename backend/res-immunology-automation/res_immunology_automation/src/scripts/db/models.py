from sqlalchemy import Column, String,Integer, DateTime
from .database import Base


class Target(Base):
    __tablename__ = "target"

    id = Column(String, primary_key=True, index=True)
    file_path = Column(String, nullable=False)  # Required attribute


class Disease(Base):
    __tablename__ = "disease"

    id = Column(String, primary_key=True, index=True)
    file_path = Column(String, nullable=False)  # Required attribute


class TargetDisease(Base):
    __tablename__ = "target_disease"

    id = Column(String, primary_key=True, index=True)
    file_path = Column(String, nullable=False)  # Required attribute

class DiseasesDossierStatus(Base):
    __tablename__ = "disease_dossier_status"

    id = Column(String, primary_key=True, index=True)
    status = Column(String, nullable=False)
    submission_time = Column(DateTime(timezone=True), nullable=True)  
    processed_time = Column(DateTime(timezone=True), nullable=True) 

class Admin(Base):
    __tablename__ = "admin"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(String, unique=True, nullable=False)  # Unique and required
    password = Column(String, nullable=False)  # Required