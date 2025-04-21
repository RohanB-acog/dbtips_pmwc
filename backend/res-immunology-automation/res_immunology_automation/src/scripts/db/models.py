from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON
from .database import Base
import tzlocal
from datetime import datetime

class Target(Base):
    __tablename__ = "target"

    id = Column(String, primary_key=True, index=True)
    file_path = Column(String, nullable=False)

class Disease(Base):
    __tablename__ = "disease"

    id = Column(String, primary_key=True, index=True)
    file_path = Column(String, nullable=False)

class TargetDisease(Base):
    __tablename__ = "target_disease"

    id = Column(String, primary_key=True, index=True)
    file_path = Column(String, nullable=False)

class DiseasesDossierStatus(Base):
    __tablename__ = "disease_dossier_status"

    id = Column(String, primary_key=True, index=True)
    status = Column(String, nullable=False)
    submission_time = Column(DateTime(timezone=True), nullable=True)
    processed_time = Column(DateTime(timezone=True), nullable=True)

class Admin(Base):
    __tablename__ = "admin"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

class DiseaseOperationHistory(Base):
    __tablename__ = "disease_operation_history"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    disease_id = Column(String, nullable=False, index=True)
    operation_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(tzlocal.get_localzone()))
    notes = Column(String, nullable=True)
    database_status = Column(String, nullable=True)
    processed_time = Column(DateTime(timezone=True), nullable=True)

class DiseaseDiffReport(Base):
    __tablename__ = "disease_diff_report"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    disease_id = Column(String, nullable=False, index=True)
    backup_file = Column(String, nullable=False)
    current_file = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(tzlocal.get_localzone()))
    changes_detected = Column(Boolean, nullable=False)
    sections = Column(JSON, nullable=False)