#build_dossier.py
from db.database import get_db # , engine, Base, SessionLocal
from db.models import DiseasesDossierStatus 
from db.database import Base

from api_models import DiseasesRequest, DiseaseRequest
from api import get_evidence_literature_semaphore, get_mouse_studies, \
                get_network_biology_semaphore, get_top_10_literature, \
                get_diseases_profiles, get_indication_pipeline_semaphore, \
                get_kol, get_key_influencers, get_rna_sequence_semaphore, \
                get_disease_ontology
                
import logging
import time
import asyncio
from graphrag_service import get_redis
from fastapi import HTTPException
from sqlalchemy.sql import func
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import update
import os, sys
import tzlocal
from datetime import datetime, timezone



logging.basicConfig(
    filename="cached_data_json/logs/build_dossier.log",  # Log file location
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

task_started = False
WAIT_TIME = 200

POSTGRES_USER: str = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
POSTGRES_DB: str = os.getenv("POSTGRES_DB")
POSTGRES_HOST: str = os.getenv("POSTGRES_HOST")

if any(var is None for var in [POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_HOST]):
    logging.info("Connection parameters not configured properly")
    sys.exit()

# Define the PostgreSQL database URL using environment variables
SQLALCHEMY_DATABASE_URL: str = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession
)

async def create_models():
    # This will create the tables for all models defined with Base
    # Base.metadata.create_all(bind=engine)
    async with engine.begin() as conn:  # `engine.begin()` ensures the connection is properly initialized
        await conn.run_sync(Base.metadata.create_all)

async def build_dossier():
    print("dossier started")
    global task_started
    if task_started:
        return  # Prevent multiple instances from starting
    task_started = True

    # db = get_db()
    while True:

        async with SessionLocal() as db:
            print("connection created")
            # processing_records = await db.execute(select(DiseasesDossierStatus).filter(DiseasesDossierStatus.status == "processing")).all()
            result = await db.execute(
                select(DiseasesDossierStatus).where(DiseasesDossierStatus.status == "processing")
            )
            processing_records = result.scalars().all()

            processing_records = [record.id for record in processing_records if record]
            logging.info(f"Processing jobs: {processing_records}")
            try:
                if not processing_records:
                    pending_jobs = []
                    result = await db.execute(
                        select(DiseasesDossierStatus).where(
                            DiseasesDossierStatus.status.in_(["error", "submitted"])
                        )
                    )
                    disease_records = result.scalars().all()
                    if disease_records:
                        for disease in disease_records:
                            pending_jobs.append(disease.id)

                    print("pending jobs: ", pending_jobs)
                    for disease in pending_jobs:
                        disease_arr = []
                        disease_arr.append(disease)
                        print("processing jobs: ",disease_arr)
                        local_time = datetime.now(tzlocal.get_localzone())

                        #change the status of current building disease to processing and processing_time
                        update_stmt = (
                            update(DiseasesDossierStatus)
                            .where(DiseasesDossierStatus.id == disease)
                            .values(status="processing", submission_time=local_time)
                        )
                        await db.execute(update_stmt) 
                        await db.commit()
                        print("status updated to processing: ", disease_arr)
                        
                        # run all endpoints for the disease
                        build_status = await run_endpoints(disease_arr)
                        
                        # update the status and processed_time according to the build status
                        if build_status != 'error':
                            local_time = datetime.now(tzlocal.get_localzone())

                            update_stmt = (
                                update(DiseasesDossierStatus)
                                .where(DiseasesDossierStatus.id == disease)
                                .values(status=build_status, processed_time=local_time)
                            )
                        else:
                            update_stmt = (
                                update(DiseasesDossierStatus)
                                .where(DiseasesDossierStatus.id == disease)
                                .values(status=build_status)
                            )

                        await db.execute(update_stmt)
                        await db.commit()
                        logging.info(f"updated status: {disease}")

                await asyncio.sleep(WAIT_TIME)
            except Exception as e:
                logging.error(f"Error in build_dossier: {e}")

            finally:
                await db.close()
                print("connection closed")

async def run_endpoints(unique_diseases):
    
    try:
        db = next(get_db())
        # async with SessionLocal() as db:
        redis = get_redis()
        print("connection created in end points")

        # Define endpoint categories
        diseases_only_endpoints = [
            get_evidence_literature_semaphore, 
            get_mouse_studies, 
            get_network_biology_semaphore, 
            get_top_10_literature, 
            get_diseases_profiles, 
            get_indication_pipeline_semaphore, 
            get_kol, 
            get_key_influencers, 
            get_rna_sequence_semaphore
        ]

        disease_only_endpoints = [
            get_disease_ontology
        ]

        # Call diseases-only endpoints
        for endpoint in diseases_only_endpoints:
            try:
                request_data = DiseasesRequest(diseases=unique_diseases)
                logging.info(f"Calling {endpoint.__name__} with all diseases: {unique_diseases}")
                if endpoint.__name__ in ['get_network_biology_semaphore', 'get_indication_pipeline_semaphore']:
                    response = await endpoint(request_data, db=db )
                elif endpoint.__name__ in ["get_top_10_literature", 'get_key_influencers']:
                    response = await endpoint(request_data)
                else:
                    response = await endpoint(request_data, redis=redis, db=db )
                logging.info("Response received")
                
            except Exception as e:
                if isinstance(e, HTTPException) and e.status_code == 404 and 'EFO ID not found' in e.detail:
                    continue 
                logging.error(f"Error calling {endpoint.__name__} for {unique_diseases}: {e}")
                return 'error'
            await asyncio.sleep(5)

        # Call disease-only endpoints
        for disease in unique_diseases:
            for endpoint in disease_only_endpoints:
                try:
                    request_data = DiseaseRequest(disease=disease)
                    logging.info(f"Calling {endpoint.__name__} for disease: {disease}")
                    response = await endpoint(request_data, redis=redis, db=db )
                except Exception as e:
                    logging.error(f"Error calling {endpoint.__name__} for disease {disease}: {e}")
                    return 'error'
        await asyncio.sleep(5)
        
        return 'processed'

    finally:
        db.close()
        print("connection closed in endpoints")

async def main():
    """Main entry point to initialize database and start dossier processing."""
    await create_models()
    await build_dossier()


if __name__ == "__main__":
    # time.sleep(100)
    asyncio.run(main())
