import os
from urllib import response
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from dependencies import get_neo4j_driver
from collections import defaultdict
from graphrag_service import get_graphrag_answer, fetch_text_chunks
from component_services.disease_profile_services import (
    create_adjacency_list,
    create_reverse_adjacency_list,
    find_ancestors,
    extract_data_by_ids
)
import uvicorn
import logging
from graphrag_service import get_redis
from redis import Redis
import json
import requests
from typing import *
from gql_variables import DiseaseAnnotationQueryVariables, SearchQuery
from gql_queries import TargetExpressionQuery
from os import getenv
from services import (
    parse_target_introduction,
    parse_target_description,
    parse_taxonomy,
    parse_targetability,
    parse_gene_map,
    parse_tractability,
    parse_gene_ontology,
    parse_mouse_phenotypes,
    parse_paralogs,
    parse_protein_expression,
    parse_subcellular,
    parse_knowndrugs,
    parse_publications,
    fetch_and_parse_diseases_known_drugs,
    fetch_and_parse_publications_for_target
    # fetch_disease_profile,
    # parse_disease_association,
    # parse_safety_events,
)
from api_models import TargetRequest, GraphRequest, DiseaseRequest, SearchQueryModel, DiseasesRequest, SearchRequest, \
    TargetOnlyRequest,ExcelExportRequest
from utils import format_for_cytoscape, get_efo_id, find_disease_id_by_name, send_graphql_request, \
    save_response_to_file, load_response_from_file, calculate_expiry_date, add_years, save_big_response_to_file,get_associated_targets,get_mouse_phenotypes,fetch_all_publications,get_exact_synonyms,get_conver_later_strapi,get_target_indication_pairs_strapi,enrich_disease_pathway_results,add_pipeline_indication_records,fetch_nct_titles
from dependencies import get_neo4j_driver
from target_analyzer import TargetAnalyzer
from db.database import get_db, engine, Base, SessionLocal
from sqlalchemy.orm import Session
from db.models import Target, Disease, TargetDisease, DiseasesDossierStatus
from component_services.market_intelligence_service import extract_nct_ids, fetch_data_for_diseases, \
    get_key_influencers_by_disease,filter_indication_records_by_synonyms,get_pmids_for_nct_ids,add_outcome_status,get_indication_pipeline_strapi,get_disease_pmid_nct_mapping,get_pmids_for_nct_ids_target_pipeline,add_outcome_status_target_pipeline,get_target_pipeline_strapi,remove_duplicates,remove_duplicates_from_indication_pipeline,get_outcome_status_openai
from component_services.evidence_services import build_query, get_geo_data_for_diseases,fetch_mouse_models,fetch_and_filter_figures_by_disease_and_pmids,fetch_mouse_model_data_alliancegenome,get_top_10_literature_helper,add_platform_name,add_study_type, get_mesh_term_for_disease
from component_services.disease_profile_llm import disease_interpreter
from component_services.target_services import find_matching_screens_for_target,fetch_subcellular_locations
from fastapi.testclient import TestClient
from fastapi.security import OAuth2PasswordRequestForm
from login_utils import create_access_token,authenticate_user,ACCESS_TOKEN_EXPIRE_MINUTES,get_current_user_role
from fastapi import status
from datetime import datetime, timedelta
from component_services.evidence_services import search_pubmed,search_pubmed_target,fetch_literature_details_in_batches,get_network_biology_strapi
from component_services.disease_profile_services import get_disease_description_strapi
from component_services.excel_export import process_data_and_return_file_rna,process_pipeline_data,process_mouse_studies,process_patent_data,process_model_studies,process_target_pipeline,process_cover_letter_list_excel
from fastapi.responses import FileResponse
from cache_results import cache_all_data
from component_services.genomics_services import fetch_pgs_data
from component_services.entity_search_services import lexical_phenotype_search, get_db_connection, get_gene_search_db_connection, lexical_gene_search
import duckdb
from duckdb import DuckDBPyConnection
from component_services.gwas_services import get_gwas_studies
from component_services.locus_zoom_services import load_data
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from fastapi.responses import FileResponse
import time
import threading
from threading import Lock
import asyncio
import httpx



app = FastAPI()

client = TestClient(app)


SERP_API_KEY: str = os.getenv('SERP_API_KEY')
SERP_API_URL: str = "https://serpapi.com/search.json"
GWAS_DATA_DIR = "/app/res-immunology-automation/res_immunology_automation/src/gwas_data"


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/gwas-data", StaticFiles(directory=GWAS_DATA_DIR), name="gwas-data")



@app.on_event("startup")
async def startup():
    # This will create the tables for all models defined with Base
    Base.metadata.create_all(bind=engine)


# def get_redis() -> Redis:
#     return Redis(host='redis', port=6379, decode_responses=True)
########################## Setting Rate Limit Locks #######################
rate_limited_until = 0
rate_limited_lock = Lock()
RATE_LIMIT = 300
WAIT_TIME = 200


pending_tasks = []
task_started = False

def is_rate_limited() -> bool:
    """Check if the system is currently rate-limited."""
    global rate_limited_until
    return time.time() < rate_limited_until


def set_rate_limit(duration: int):
    """Set the rate limit for a specified duration."""
    global rate_limited_until
    with rate_limited_lock:
        rate_limited_until = time.time() + duration

############################################################################

def generate_cache_key(endpoint: str, target: str, diseases: List[str] = None) -> str:
    if diseases is None:
        diseases_str = ""
    else:
        diseases_str = "_".join(diseases)

    return f"{endpoint}:{target}:{diseases_str}"


async def get_cached_response(redis: Redis, key: str):
    cached_response = redis.json().get(key)
    if cached_response:
        # logger.log("")
        # return json.loads(cached_response)
        return cached_response
    return None


async def set_cached_response(redis: Redis, key: str, response: dict):
    #redis.set(key, json.dumps(response), ex=expiry)
    redis.json().set(key, "$", response)


def validate_target_and_diseases(request: TargetRequest, require_diseases: bool = False):
    target = request.target.strip()
    diseases = request.diseases

    if not target:
        raise HTTPException(status_code=400, detail="Target gene name is required.")

    if require_diseases and not diseases:
        raise HTTPException(status_code=400, detail="At least one disease must be provided.")

    return target, diseases


@app.get("/")
async def read_root():
    return {"message": "Backend is running"}

@app.get("/api/download/{file_path}")
async def download_file(file_path: str):
   
    full_path = os.path.join(GWAS_DATA_DIR, file_path)
    if os.path.isfile(full_path):
        return FileResponse(path=full_path, filename=os.path.basename(full_path))
    else:
        raise HTTPException(status_code=404, detail="File not found")


#################################### Build Dossier ##############################################

@app.post("/dossier/disease-dossier-status/", tags = ["Dossier Status"])
async def get_dossier_status(request: DiseasesRequest, db: Session = Depends(get_db)):
    try:
        diseases = request.diseases
        cached_diseases = []
        building_dossier = []
        errors = []
        for disease in diseases:
            disease = disease.lower().strip()
            disease_record = db.query(DiseasesDossierStatus).filter_by(id=f"{disease}").first()
            if disease_record is not None:
                cache_status: str = disease_record.status
                if cache_status == 'processed':
                    cached_diseases.append(disease) 
                elif cache_status in ['processing','submitted','error']:
                    building_dossier.append(disease) 
                              
            else:
                new_record = DiseasesDossierStatus(id=f"{disease}",
                                    status="submitted")  # Create a new instance of the identified model
                db.add(new_record)  # Add the new record to the session
                db.commit()  # Commit the transaction to save the record to the database
                db.refresh(new_record) 
                logging.info(f"added record for disease {disease}")
                building_dossier.append(disease)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    
    
    return {"cached diseases":cached_diseases, "building diseases": building_dossier}

# dossier_semaphore = asyncio.Semaphore(1)

@app.get("/dossier/dashboard/", tags = ["Dossier Status"])
async def get_dossier_dashboard(db: Session = Depends(get_db)):
    try:
        response = {}

        def fetch_records_by_status(record_status: str) -> List[Dict[str, str]]:
            all_records = []
            records = db.query(DiseasesDossierStatus).filter_by(status=record_status).all()
            for record in records:
                data = {}
                data['disease'] = record.id
                data['submission_time'] = record.submission_time
                data['processed_time'] = record.processed_time
                all_records.append(data)
            return all_records

        status_list = ['submitted', 'processing', 'processed', 'error']
        for status in status_list:
            response[status] = fetch_records_by_status(status)

        

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))    
    
    return response

#################################### target details page ##############################################


@app.post("/target-profile/details/", tags=["Target Profile"])
async def get_target_details(request: TargetOnlyRequest, redis: Redis = Depends(get_redis),
                             db: Session = Depends(get_db)):
    target: str = request.target.strip().lower()
    key: str = f"/target-profile/details/:{target}"
    endpoint: str = "/target-profile/details/"

    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/target"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    # File path for the JSON response
    file_path: str = os.path.join(cache_dir, f"{target}.json")

    target_record = db.query(Target).filter_by(id=target).first()
    # 1. Check if the cached JSON file exists
    if target_record is not None:
        cached_file_path: str = target_record.file_path
        print(f"Loading cached response from file: {cached_file_path}")
        cached_responses: Dict = load_response_from_file(cached_file_path)

        # Check if the endpoint response exists in the cached data
        if f"{endpoint}" in cached_responses:
            print(f"Returning cached response from file: {cached_file_path}")
            return cached_responses[f"{endpoint}"]

    cached_response_redis = await get_cached_response(redis, key)
    if cached_response_redis:
        print("Returning redis cached response")
        return cached_response_redis

    analyzer = TargetAnalyzer(target)

    try:
        introduction = analyzer.get_target_introduction()
        description = analyzer.get_target_description()
        taxonomy = analyzer.get_target_introduction()

        parsed_introduction = parse_target_introduction(introduction)
        parsed_description = parse_target_description(description)
        parsed_taxonomy = parse_taxonomy(taxonomy)

        target_details = {
            "ensembl_id": analyzer.ensembl_id,
            "hgnc_id": analyzer.hgnc_id,
            "uniprot_id": analyzer.uniprot_id
        }
        response = {
            "target_details": target_details,
            "introduction": parsed_introduction,
            "summary_and_characteristics": parsed_description,
            "taxonomy": parsed_taxonomy,
        }
        await set_cached_response(redis, key, response)

        if target_record is not None:
            cached_responses = load_response_from_file(cached_file_path)
        else:
            cached_responses = {}

        cached_responses[f"{endpoint}"] = response

        if target_record is None:
            save_response_to_file(file_path, cached_responses)
            new_record = Target(id=target, file_path=file_path)  # Create a new instance of the identified model
            db.add(new_record)  # Add the new record to the session
            db.commit()  # Commit the transaction to save the record to the database
            db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
            # fields)
            print(f"Record with ID {target} added to the target table.")
        else:
            save_response_to_file(cached_file_path, cached_responses)

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/target-profile/ontology/", tags=["Target Profile"])
async def get_ontology(request: TargetOnlyRequest, redis: Redis = Depends(get_redis), db: Session = Depends(get_db)):
    target: str = request.target.strip().lower()
    key: str = f"/target-profile/ontology/:{target}"
    endpoint: str = "/target-profile/ontology/"

    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/target"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    # File path for the JSON response
    file_path: str = os.path.join(cache_dir, f"{target}.json")

    target_record = db.query(Target).filter_by(id=target).first()
    # 1. Check if the cached JSON file exists
    if target_record is not None:
        cached_file_path: str = target_record.file_path
        print(f"Loading cached response from file: {cached_file_path}")
        cached_responses: Dict = load_response_from_file(cached_file_path)

        # Check if the endpoint response exists in the cached data
        if f"{endpoint}" in cached_responses:
            print(f"Returning cached response from file: {cached_file_path}")
            return cached_responses[f"{endpoint}"]

    cached_response_redis = await get_cached_response(redis, key)
    if cached_response_redis:
        print("Returning redis cached response")
        return cached_response_redis

    analyzer = TargetAnalyzer(target)
    try:
        ontology = analyzer.get_target_ontology()
        parsed_ontology = parse_gene_ontology(ontology)
        response = {
            "ontology": parsed_ontology
        }

        await set_cached_response(redis, key, response)

        if target_record is not None:
            cached_responses = load_response_from_file(cached_file_path)
        else:
            cached_responses = {}

        cached_responses[f"{endpoint}"] = response

        if target_record is None:
            save_response_to_file(file_path, cached_responses)
            new_record = Target(id=target, file_path=file_path)  # Create a new instance of the identified model
            db.add(new_record)  # Add the new record to the session
            db.commit()  # Commit the transaction to save the record to the database
            db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
            # fields)
            print(f"Record with ID {target} added to the target table.")
        else:
            save_response_to_file(cached_file_path, cached_responses)

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/target-profile/protein-expressions/", tags=["Target Profile"])
async def get_protein_expressions(request: TargetOnlyRequest, redis: Redis = Depends(get_redis),
                                  db: Session = Depends(get_db)):
    target: str = request.target.strip().lower()
    key: str = f"/target-profile/protein-expressions/:{target}"
    endpoint: str = "/target-profile/protein-expressions/"

    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/target"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    # File path for the JSON response
    file_path: str = os.path.join(cache_dir, f"{target}.json")

    target_record = db.query(Target).filter_by(id=target).first()
    # 1. Check if the cached JSON file exists
    if target_record is not None:
        cached_file_path: str = target_record.file_path
        print(f"Loading cached response from file: {cached_file_path}")
        cached_responses: Dict = load_response_from_file(cached_file_path)

        # Check if the endpoint response exists in the cached data
        if f"{endpoint}" in cached_responses:
            print(f"Returning cached response from file: {cached_file_path}")
            return cached_responses[f"{endpoint}"]

    cached_response_redis = await get_cached_response(redis, key)
    if cached_response_redis:
        print("Returning redis cached response")
        return cached_response_redis

    analyzer = TargetAnalyzer(target)
    try:
        expressions = analyzer.get_differential_rna_and_protein_expression()
        parsed_protein_expressions = parse_protein_expression(expressions['data']['target']['expressions'])
        response = {
            "protein_expressions": parsed_protein_expressions
        }

        await set_cached_response(redis, key, response)

        if target_record is not None:
            cached_responses = load_response_from_file(cached_file_path)
        else:
            cached_responses = {}

        cached_responses[f"{endpoint}"] = response

        if target_record is None:
            save_response_to_file(file_path, cached_responses)
            new_record = Target(id=target, file_path=file_path)  # Create a new instance of the identified model
            db.add(new_record)  # Add the new record to the session
            db.commit()  # Commit the transaction to save the record to the database
            db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
            # fields)
            print(f"Record with ID {target} added to the target table.")
        else:
            save_response_to_file(cached_file_path, cached_responses)

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/target-profile/subcellular/", tags=["Target Profile"])
async def get_subcellular(request: TargetOnlyRequest, redis: Redis = Depends(get_redis), db: Session = Depends(get_db)):
    target: str = request.target.strip().lower()
    key: str = f"/target-profile/subcellular/:{target}"
    endpoint: str = "/target-profile/subcellular/"

    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/target"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    # File path for the JSON response
    file_path: str = os.path.join(cache_dir, f"{target}.json")

    target_record = db.query(Target).filter_by(id=target).first()
    # 1. Check if the cached JSON file exists
    if target_record is not None:
        cached_file_path: str = target_record.file_path
        print(f"Loading cached response from file: {cached_file_path}")
        cached_responses: Dict = load_response_from_file(cached_file_path)

        # Check if the endpoint response exists in the cached data
        if f"{endpoint}" in cached_responses:
            print(f"Returning cached response from file: {cached_file_path}")
            return cached_responses[f"{endpoint}"]

    cached_response_redis = await get_cached_response(redis, key)
    if cached_response_redis:
        print("Returning redis cached response")
        return cached_response_redis

    analyzer = TargetAnalyzer(target)
    try:
        uniprot_id: str=analyzer.get_uniprotkb_id(target)
        if not uniprot_id:
            response = {
            "subcellular": [],
            "subcellular_locations":[]
            }
        else:
            topology = analyzer.get_target_topology_features()
            if not topology:
                parsed_subcellular=[]
            else:
                parsed_subcellular = parse_subcellular(topology)
            response = {
                "subcellular": parsed_subcellular,
                "subcellular_locations":fetch_subcellular_locations(uniprot_id)
            }

        await set_cached_response(redis, key, response)

        if target_record is not None:
            cached_responses = load_response_from_file(cached_file_path)
        else:
            cached_responses = {}

        cached_responses[f"{endpoint}"] = response

        if target_record is None:
            save_response_to_file(file_path, cached_responses)
            new_record = Target(id=target, file_path=file_path)  # Create a new instance of the identified model
            db.add(new_record)  # Add the new record to the session
            db.commit()  # Commit the transaction to save the record to the database
            db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
            # fields)
            print(f"Record with ID {target} added to the target table.")
        else:
            save_response_to_file(cached_file_path, cached_responses)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/target-profile/anatomical-system/", tags=["Target Profile"])
async def get_anatomy(request: TargetOnlyRequest, redis: Redis = Depends(get_redis), db: Session = Depends(get_db)):
    target: str = request.target.strip().lower()
    key: str = f"/target-profile/anatomical-system/:{target}"
    endpoint: str = "/target-profile/anatomical-system/"

    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/target"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    # File path for the JSON response
    file_path: str = os.path.join(cache_dir, f"{target}.json")

    target_record = db.query(Target).filter_by(id=target).first()
    # 1. Check if the cached JSON file exists
    if target_record is not None:
        cached_file_path: str = target_record.file_path
        print(f"Loading cached response from file: {cached_file_path}")
        cached_responses: Dict = load_response_from_file(cached_file_path)

        # Check if the endpoint response exists in the cached data
        if f"{endpoint}" in cached_responses:
            print(f"Returning cached response from file: {cached_file_path}")
            return cached_responses[f"{endpoint}"]

    cached_response_redis = await get_cached_response(redis, key)
    if cached_response_redis:
        print("Returning redis cached response")
        return cached_response_redis

    analyzer = TargetAnalyzer(target)
    try:
        ensemble_id: str = analyzer.get_ensembl_id(target)
        print("ensemble_id: ", ensemble_id)

        ot_api_url: str = "https://api.platform.opentargets.org/api/v4/graphql"

        variables: dict = {"ensemblId": ensemble_id}

        # Make a POST request to the GraphQL API
        response = requests.post(
            ot_api_url,
            json={"query": TargetExpressionQuery, "variables": variables}
        )
        response = response.json()

        await set_cached_response(redis, key, response)

        if target_record is not None:
            cached_responses = load_response_from_file(cached_file_path)
        else:
            cached_responses = {}

        cached_responses[f"{endpoint}"] = response

        if target_record is None:
            save_response_to_file(file_path, cached_responses)
            new_record = Target(id=target, file_path=file_path)  # Create a new instance of the identified model
            db.add(new_record)  # Add the new record to the session
            db.commit()  # Commit the transaction to save the record to the database
            db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
            # fields)
            print(f"Record with ID {target} added to the target table.")
        else:
            save_response_to_file(cached_file_path, cached_responses)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/target-profile/protein-structure/", tags=["Target Profile"])
async def get_protein_structure(request: TargetOnlyRequest, redis: Redis = Depends(get_redis),
                                db: Session = Depends(get_db)):
    target: str = request.target.strip().lower()
    key: str = f"/target-profile/protein-structure/:{target}"
    endpoint: str = "/target-profile/protein-structure/"

    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/target"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    # File path for the JSON response
    file_path: str = os.path.join(cache_dir, f"{target}.json")

    target_record = db.query(Target).filter_by(id=target).first()
    # 1. Check if the cached JSON file exists
    if target_record is not None:
        cached_file_path: str = target_record.file_path
        print(f"Loading cached response from file: {cached_file_path}")
        cached_responses: Dict = load_response_from_file(cached_file_path)

        # Check if the endpoint response exists in the cached data
        if f"{endpoint}" in cached_responses:
            print(f"Returning cached response from file: {cached_file_path}")
            return cached_responses[f"{endpoint}"]

    cached_response_redis = await get_cached_response(redis, key)
    if cached_response_redis:
        print("Returning redis cached response")
        return cached_response_redis

    analyzer = TargetAnalyzer(target)
    try:
        uniprot_id: str = analyzer.get_uniprotkb_id(target)
        print("uniprot_id: ", uniprot_id)

        ebi_protein_api_url: str = "https://www.ebi.ac.uk/proteins/api/proteins/"
        request_url: str = f"{ebi_protein_api_url}{uniprot_id}"

        # Make a POST request to the GraphQL API
        response = requests.get(request_url)
        response = response.json()

        await set_cached_response(redis, key, response)

        if target_record is not None:
            cached_responses = load_response_from_file(cached_file_path)
        else:
            cached_responses = {}

        cached_responses[f"{endpoint}"] = response

        if target_record is None:
            save_response_to_file(file_path, cached_responses)
            new_record = Target(id=target, file_path=file_path)  # Create a new instance of the identified model
            db.add(new_record)  # Add the new record to the session
            db.commit()  # Commit the transaction to save the record to the database
            db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
            # fields)
            print(f"Record with ID {target} added to the target table.")
        else:
            save_response_to_file(cached_file_path, cached_responses)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#################################### market intelligence page ##############################################
semaphore = asyncio.Semaphore(1)
@app.post("/market-intelligence/target-pipeline-semaphore/", tags=["Market Intelligence"])
async def get_target_pipeline_semaphore(request: TargetRequest, redis: Redis = Depends(get_redis), db: Session = Depends(get_db)):
    try:
        async with semaphore:  # This will block concurrent requests
            print(f"lock applied and processing {request.diseases}")
            response =  await get_target_pipeline(request, redis, db)
            print("lock removed")
    except Exception as e:
        raise e
    return response


@app.post("/market-intelligence/target-pipeline/", tags=["Market Intelligence"])
async def get_target_pipeline(request: TargetRequest, redis: Redis = Depends(get_redis), db: Session = Depends(get_db)):
    target, diseases = validate_target_and_diseases(request, require_diseases=True)
    key = generate_cache_key("/market-intelligence/target-pipeline/", request.target, request.diseases)
    target: str = request.target.strip().lower()
    diseases: List[str] = [d.strip().lower().replace(" ", "_") for d in request.diseases]

    endpoint: str = "/market-intelligence/target-pipeline/"
    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/target_disease"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    # File path for the JSON response
    # file_path: str = os.path.join(cache_dir, f"{target}.json")
    cached_diseases: Set[str] = set()
    cached_data: List = []
    for disease in diseases:
        target_disease_record = db.query(TargetDisease).filter_by(id=f"{target}-{disease}").first()
        # 1. Check if the cached JSON file exists
        if target_disease_record is not None:
            cached_file_path: str = target_disease_record.file_path
            print(f"Loading cached response from file: {cached_file_path}")
            cached_responses: Dict = load_response_from_file(cached_file_path)

            # Check if the endpoint response exists in the cached data
            if f"{endpoint}" in cached_responses:
                cached_diseases.add(disease)
                print(f"Returning cached response from file: {cached_file_path}")
                cached_data.extend(cached_responses[f"{endpoint}"]["target_pipeline"])

    # filtering diseases whose response is not present in the json file
    filtered_diseases = [disease for disease in diseases if disease not in cached_diseases]
    print("filtered_diseases: ", filtered_diseases)
    if len(filtered_diseases) == 0:  # all pairs fo target and disease already present in the json file
        response = {"target_pipeline": cached_data}
        print("All pair of target and disease already present in cached json files,returning cached response")
        await set_cached_response(redis, key, response)
        return response

    redis_cached_response = await get_cached_response(redis, key)
    if redis_cached_response:
        print("Returning redis cached response")
        return redis_cached_response

    analyzer = TargetAnalyzer(target)

    try:
        if is_rate_limited():
            remaining_time = int(rate_limited_until - time.time())
            raise HTTPException(status_code=429, detail=f"Rate limit in effect. Try again after {remaining_time} seconds.")

        knowndrugs = analyzer.get_known_drugs()
        target_pipeline = parse_knowndrugs(knowndrugs, [disease.replace('_', ' ') for disease in
                                                        filtered_diseases])  # only pass the disease for which data is
        print("parse_knowndrugs\n")
        strapi_results=get_target_pipeline_strapi([disease.replace('_', ' ') for disease in
                                                        filtered_diseases],target)
        target_pipeline.extend(strapi_results)
        print("Added strapi results\n")
        for entry in target_pipeline:
            entry["NctIdTitleMapping"]=fetch_nct_titles([url.split("/")[-1] for url in entry.get("Source URLs",[])])
        disease_pmid_nct_mapping=get_disease_pmid_nct_mapping([disease.replace('_', ' ') for disease in
                                                        filtered_diseases])
        print("get_disease_pmid_nct_mapping\n")
        print(disease_pmid_nct_mapping)
        target_pipeline=get_pmids_for_nct_ids_target_pipeline(target_pipeline,disease_pmid_nct_mapping)
        print("get_pmids_for_nct_ids_target_pipeline\n")
        target_pipeline=add_outcome_status_target_pipeline(target_pipeline)
        print("add_outcome_status_target_pipeline\n")
        # not cached in json file
        print("target_pipeline:", target_pipeline)

        for record in target_pipeline:
            disease: str = record["Disease"].strip().lower().replace(" ", "_")
            target_disease_record = db.query(TargetDisease).filter_by(id=f"{target}-{disease}").first()
            file_path: str = os.path.join(cache_dir, f"{target}-{disease}.json")

            # now add the response of each of the disease into lookup table.
            if target_disease_record is not None:
                cached_file_path: str = target_disease_record.file_path
                cached_responses = load_response_from_file(cached_file_path)
            else:
                cached_responses = {}

            # Check if 'target_pipeline' exists for the given endpoint
            if f"{endpoint}" in cached_responses and "target_pipeline" in cached_responses[f"{endpoint}"]:
                # If it exists, append the record to the existing list
                cached_responses[f"{endpoint}"]["target_pipeline"].append(record)
            else:
                # If 'target_pipeline' doesn't exist, initialize it with the record in a new list
                cached_responses[f"{endpoint}"] = {"target_pipeline": [record]}

            if target_disease_record is None:
                save_response_to_file(file_path, cached_responses)
                new_record = TargetDisease(id=f"{target}-{disease}",
                                           file_path=file_path)  # Create a new instance of the identified model
                db.add(new_record)  # Add the new record to the session
                db.commit()  # Commit the transaction to save the record to the database
                db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
                # fields)
                print(f"Record with ID {target}-{disease} added to the target_disease table.")
            else:
                save_response_to_file(cached_file_path, cached_responses)

        target_pipeline.extend(cached_data)
        target_pipeline=remove_duplicates(target_pipeline)
        response = {"target_pipeline": target_pipeline}

        await set_cached_response(redis, key, response)
        return response
    except Exception as e:
        status_code = getattr(e, "status_code", None)
        if status_code == 429:
            set_rate_limit(RATE_LIMIT)
            raise e
        raise HTTPException(status_code=500, detail=str(e))

semaphore = asyncio.Semaphore(1)
@app.post("/market-intelligence/indication-pipeline-semaphore/", tags=["Market Intelligence"])
async def get_indication_pipeline_semaphore(request: DiseasesRequest,
                                  db: Session = Depends(get_db)):
    try:
        async with semaphore:  # This will block concurrent requests
            print(f"lock applied and processing {request.diseases}")
            response =  await get_indication_pipeline(request, db)
        print("lock removed")
    except Exception as e:
        raise e
    return response    

@app.post("/market-intelligence/indication-pipeline/", tags=["Market Intelligence"])
async def get_indication_pipeline(request: DiseasesRequest,
                                  db: Session = Depends(get_db)):
    diseases = request.diseases
    diseases: List[str] = [d.strip().lower().replace(" ", "_") for d in request.diseases]
    diseases_str = "-".join(diseases)
    key: str = f"/market-intelligence/indication-pipeline:{diseases_str}"
    endpoint: str = "/market-intelligence/indication-pipeline/"
    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/disease"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists
    cached_diseases: Set[str] = set()
    cached_data: List = []
    for disease in diseases:
        disease_record = db.query(Disease).filter_by(id=f"{disease}").first()
        # 1. Check if the cached JSON file exists
        if disease_record is not None:
            cached_file_path: str = disease_record.file_path
            print(f"Loading cached response from file: {cached_file_path}")
            cached_responses: Dict = load_response_from_file(cached_file_path)

            # Check if the endpoint response exists in the cached data
            if f"{endpoint}" in cached_responses:
                cached_diseases.add(disease)
                print(f"Returning cached response from file: {cached_file_path}")
                cached_data.append(cached_responses[f"{endpoint}"]["indication_pipeline"])

    # filtering diseases whose response is not present in the json file
    filtered_diseases = [disease for disease in diseases if disease not in cached_diseases]
    print("filtered_diseases: ", filtered_diseases)
    
    diseases_and_efo = {}
    for disease_name in filtered_diseases:
        disease_name = disease_name.replace("_", " ")
        efo_id = get_efo_id(disease_name)
        if efo_id:
            diseases_and_efo[disease_name] = efo_id
        else:
            raise HTTPException(status_code=404, detail=f"EFO ID not found for {disease_name}")

    cached_response_api: Dict = {}
    for data in cached_data:
        disease_key, value = list(data.items())[0]
        if "indication_pipeline" not in cached_response_api:
            cached_response_api["indication_pipeline"] = {}
        cached_response_api["indication_pipeline"][disease_key] = value
    
    # cached_response_api=add_pipeline_indication_records({disease.replace("_"," ") for disease in cached_diseases},cached_response_api)
    if len(filtered_diseases) == 0:  # all pairs fo target and disease already present in the json file
        print("All pair of target and disease already present in cached json files,returning cached response")
        return cached_response_api


    try:
        if is_rate_limited():
            remaining_time = int(rate_limited_until - time.time())
            raise HTTPException(status_code=429, detail=f"Rate limit in effect. Try again after {remaining_time} seconds.")
    
        disease_exact_synonyms:Dict[str,List[str]]={}
        for d in diseases_and_efo.keys():
            disease_exact_synonyms[d]=get_exact_synonyms(d)
        print("disease_exact_synonyms\n")
        print(f"{disease_exact_synonyms}")
        indication_pipeline:Dict[str, List[Dict]] = fetch_and_parse_diseases_known_drugs(diseases_and_efo,disease_exact_synonyms)
        print("fetch_and_parse_diseases_known_drugs\n")
        # adding strapi data
        for disease_name,values in indication_pipeline.items():
            values.extend(get_indication_pipeline_strapi(disease_name))
        for disease_name,entries in indication_pipeline.items():
            for entry in entries:
                entry["NctIdTitleMapping"]=fetch_nct_titles([url.split("/")[-1] for url in entry.get("Source URLs",[])])

                
        indication_pipeline=get_pmids_for_nct_ids(indication_pipeline)
        print("get_pmids_for_nct_ids\n")
        indication_pipeline=add_outcome_status(indication_pipeline)
        print("add_outcome_status\n")
        response = {"indication_pipeline": indication_pipeline}
        for disease, value in response["indication_pipeline"].items():
            disease = disease.strip().lower().replace(" ", "_")
            disease_record = db.query(Disease).filter_by(id=f"{disease}").first()
            file_path: str = os.path.join(cache_dir, f"{disease}.json")

            # now add the response of each of the disease into lookup table.
            if disease_record is not None:
                cached_file_path: str = disease_record.file_path
                cached_responses = load_response_from_file(cached_file_path)
            else:
                cached_responses = {}

            cached_responses[f"{endpoint}"] = {"indication_pipeline": {disease.replace("_", " "): value}}

            if disease_record is None:
                save_response_to_file(file_path, cached_responses)
                new_record = Disease(id=f"{disease}",
                                     file_path=file_path)  # Create a new instance of the identified model
                db.add(new_record)  # Add the new record to the session
                db.commit()  # Commit the transaction to save the record to the database
                db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
                # fields)
                print(f"Record with ID {disease} added to the target_disease table.")
            else:
                save_response_to_file(cached_file_path, cached_responses)

        
        response["indication_pipeline"].update(cached_response_api.get("indication_pipeline", {}))
        response["indication_pipeline"]=remove_duplicates_from_indication_pipeline(response["indication_pipeline"])
        # response=add_pipeline_indication_records(diseases_and_efo,response)
        return response
    
    except Exception as e:
        status_code = getattr(e, "status_code", None)
        if status_code == 429:
            set_rate_limit(RATE_LIMIT)
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/market-intelligence/kol/", tags=["Market Intelligence"])
async def get_kol(request: DiseasesRequest, redis: Redis = Depends(get_redis),
                  db: Session = Depends(get_db)):
    diseases: List[str] = request.diseases
    diseases = [s.strip().lower().replace(" ", "_") for s in diseases]
    diseases_str = "-".join(diseases)

    # Generate a cache key for the request using target and disease list
    key: str = f"/market-intelligence/kol/:{diseases_str}"
    endpoint: str = "/market-intelligence/kol/"

    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/disease"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    cached_diseases: Set[str] = set()
    cached_data: Dict = {}
    for disease in diseases:
        disease_record = db.query(Disease).filter_by(id=f"{disease}").first()
        # 1. Check if the cached JSON file exists
        if disease_record is not None:
            cached_file_path: str = disease_record.file_path
            print(f"Loading cached response from file: {cached_file_path}")
            cached_responses: Dict = load_response_from_file(cached_file_path)

            # Check if the endpoint response exists in the cached data
            if f"{endpoint}" in cached_responses:
                cached_diseases.add(disease)
                print(f"Returning cached response from file: {cached_file_path}")
                cached_data[disease.replace("_", " ")] = cached_responses[f"{endpoint}"][disease.replace("_", " ")]

    # filtering diseases whose response is not present in the json file
    filtered_diseases = [disease for disease in diseases if disease not in cached_diseases]

    if len(filtered_diseases) == 0:  # all disease already present in the json file
        print("All diseases already present in cached json files,returning cached response")
        await set_cached_response(redis, key, cached_data)
        return cached_data

    print("filtered diseases: ", filtered_diseases)
    # Check if cached response exists in Redis
    cached_response_redis: dict = await get_cached_response(redis, key)
    if cached_response_redis:
        print("Returning chached response")
        return cached_response_redis

    diseases_and_efo = {}
    for disease_name in filtered_diseases:
        disease_name = disease_name.replace("_", " ")
        efo_id = get_efo_id(disease_name)
        if efo_id:
            diseases_and_efo[disease_name] = efo_id
        else:
            raise HTTPException(status_code=404, detail=f"EFO ID not found for {disease_name}")

    try:
        # indication_pipeline = fetch_and_parse_diseases_known_drugs(diseases_and_efo)
        # response = {"indication_pipeline": indication_pipeline}
        request_data = DiseasesRequest(diseases=[s.strip().lower().replace("_", " ") for s in filtered_diseases])
        response = client.post("/market-intelligence/indication-pipeline/", json=request_data.dict())
        response = response.json()
        disease_nct_ids: Dict[str, List[Tuple[str, str]]] = extract_nct_ids(response)
        print(disease_nct_ids)
        final_response = fetch_data_for_diseases(disease_nct_ids)

        for disease, data in final_response.items():
            disease: str = disease.strip().lower().replace(" ", "_")
            disease_record = db.query(Disease).filter_by(id=f"{disease}").first()
            file_path: str = os.path.join(cache_dir, f"{disease}.json")

            # now add the response of each of the disease into lookup table.
            if disease_record is not None:
                cached_file_path: str = disease_record.file_path
                cached_responses = load_response_from_file(cached_file_path)
            else:
                cached_responses = {}

            cached_responses[f"{endpoint}"] = {disease.replace("_", " "): data}

            if disease_record is None:
                save_response_to_file(file_path, cached_responses)
                new_record = Disease(id=f"{disease}",
                                     file_path=file_path)  # Create a new instance of the identified model
                db.add(new_record)  # Add the new record to the session
                db.commit()  # Commit the transaction to save the record to the database
                db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
                # fields)
                print(f"Record with ID {disease} added to the disease table.")
            else:
                save_response_to_file(cached_file_path, cached_responses)

        final_response.update(cached_data)
        await set_cached_response(redis, key, final_response)
        return final_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/market-intelligence/key-influencers/", tags=["Market Intelligence"])
async def get_key_influencers(request: DiseasesRequest):
    """
    Fetch disease information from the loaded JSON data.
    Args:
        request (DiseaseRequest): A list of diseases to fetch data for.

    Returns:
        Dict: Disease information if available, or error message if not found.
    """
    diseases: List[str] = request.diseases
    diseases = [s.strip().lower() for s in diseases]

    # Initialize a dictionary to hold the response
    result: Dict[str, Any] = {}
    # Iterate through the requested diseases
    for disease in diseases:
        result[disease] = get_key_influencers_by_disease(disease)

    return result


#################################### evidence page ##############################################

@app.post("/evidence/target-literature/", tags=["Evidence"])
async def get_evidence_target_literature(request: TargetRequest,
                                  db: Session = Depends(get_db)):
    diseases: List[str] = request.diseases
    diseases = [s.strip().lower().replace(" ", "_") for s in diseases]
    target=request.target.strip().lower()

    # Generate a cache key for the request using target and disease list
    endpoint: str = "/evidence/target-literature/"

    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/target_disease"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    cached_diseases: Set[str] = set()
    cached_data: Dict[str,Any] = {}
    for disease in diseases:
        target_disease_record = db.query(TargetDisease).filter_by(id=f"{target}-{disease}").first()
        # 1. Check if the cached JSON file exists
        if target_disease_record is not None:
            cached_file_path: str = target_disease_record.file_path
            print(f"Loading cached response from file: {cached_file_path}")
            cached_responses: Dict = load_response_from_file(cached_file_path)

            # Check if the endpoint response exists in the cached data
            if f"{endpoint}" in cached_responses:
                cached_diseases.add(disease)
                print(f"Returning cached response from file: {cached_file_path}")
                cached_data[disease.replace("_"," ")]=cached_responses[f"{endpoint}"]

    # filtering diseases whose response is not present in the json file
    filtered_diseases = [disease for disease in diseases if disease not in cached_diseases]

    if len(filtered_diseases) == 0:  # all disease already present in the json file
        print("All diseases already present in cached json files,returning cached response")
        return cached_data

    print("filtered diseases: ", filtered_diseases)
    # Check if cached response exists in Redis
    target_terms_file: str = "../target_data/target_terms.json"

    try:
        if is_rate_limited():
            remaining_time = int(rate_limited_until - time.time())
            raise HTTPException(status_code=429, detail=f"Rate limit in effect. Try again after {remaining_time} seconds.")
    
        for disease in filtered_diseases:
            
            target_disease_record = db.query(TargetDisease).filter_by(id=f"{target}-{disease}").first()
            file_path: str = os.path.join(cache_dir, f"{target}-{disease}.json")

            # now add the response of each of the disease into lookup table.
            if target_disease_record is not None:
                cached_file_path: str = target_disease_record.file_path
                cached_responses = load_response_from_file(cached_file_path)
            else:
                cached_responses = {}
            
            pmids: List[str]=[]
            mesh_term = get_mesh_term_for_disease(disease.replace("_"," "))
            pmids=search_pubmed_target(target,disease.replace("_"," "),target_terms_file,mesh_term)
            print("pmids: ",len(pmids))
            all_literature_details: List[Dict[str,Any]] = fetch_literature_details_in_batches(disease.replace("_"," "),pmids)
            print("all_literature_details: ",len(all_literature_details))
            cached_data[disease.replace("_"," ")] = {"literature": all_literature_details}
            cached_responses[f"{endpoint}"]={"literature": all_literature_details}

            if target_disease_record is None:
                save_response_to_file(file_path, cached_responses)
                new_record = TargetDisease(id=f"{target}-{disease}", file_path=file_path)  # Create a new instance of the identified model
                db.add(new_record)  # Add the new record to the session
                db.commit()  # Commit the transaction to save the record to the database
                db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
                # fields)
                print(f"Record with ID {target}-{disease} added to the target-disease table.")
            else:
                save_response_to_file(cached_file_path, cached_responses)

        return cached_data
    except Exception as e:
        status_code = getattr(e, "status_code", None)
        if status_code == 429:
            set_rate_limit(RATE_LIMIT)
            raise e
        raise HTTPException(status_code=500, detail=str(e))

semaphore = asyncio.Semaphore(1)
@app.post("/evidence/literature-semaphore/", tags=["Evidence"])
async def get_evidence_literature_semaphore(request: DiseasesRequest, redis: Redis = Depends(get_redis),
                                  db: Session = Depends(get_db)):

    try:
        async with semaphore:  # This will block concurrent requests
            print(f"lock applied and processing {request.diseases}")
            response =  await get_evidence_literature(request, redis, db)
        print("lock removed")
    except Exception as e:
        raise e
    return response

@app.post("/evidence/literature/", tags=["Evidence"])
async def get_evidence_literature(request: DiseasesRequest, redis: Redis = Depends(get_redis),
                                  db: Session = Depends(get_db)):
    diseases: List[str] = request.diseases
    diseases = [s.strip().lower().replace(" ", "_") for s in diseases]
    diseases_str = "-".join(diseases)

    # Generate a cache key for the request using target and disease list
    key: str = f"/evidence/literature/:{diseases_str}"
    endpoint: str = "/evidence/literature/"

    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/disease"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    cached_diseases: Set[str] = set()
    cached_data: Dict[str,Any] = {}
    for disease in diseases:
        disease_record = db.query(Disease).filter_by(id=f"{disease}").first()
        # 1. Check if the cached JSON file exists
        if disease_record is not None:
            cached_file_path: str = disease_record.file_path
            print(f"Loading cached response from file: {cached_file_path}")
            cached_responses: Dict = load_response_from_file(cached_file_path)

            # Check if the endpoint response exists in the cached data
            if f"{endpoint}" in cached_responses:
                cached_diseases.add(disease)
                print(f"Returning cached response from file: {cached_file_path}")
                cached_data[disease.replace("_"," ")]=cached_responses[f"{endpoint}"]

    # filtering diseases whose response is not present in the json file
    filtered_diseases = [disease for disease in diseases if disease not in cached_diseases]

    if len(filtered_diseases) == 0:  # all disease already present in the json file
        print("All diseases already present in cached json files,returning cached response")
        await set_cached_response(redis, key, cached_data)
        return cached_data

    print("filtered diseases: ", filtered_diseases)
    # Check if cached response exists in Redis
    cached_response_redis: dict = await get_cached_response(redis, key)
    if cached_response_redis:
        print("Returning chached response")
        return cached_response_redis

    try:
        if is_rate_limited():
            remaining_time = int(rate_limited_until - time.time())
            raise HTTPException(status_code=429, detail=f"Rate limit in effect. Try again after {remaining_time} seconds.")
    
        for disease in filtered_diseases:
            print("cached data doesn't exists...Generating the data")
            disease_record = db.query(Disease).filter_by(id=f"{disease}").first()
            file_path: str = os.path.join(cache_dir, f"{disease}.json")

            # now add the response of each of the disease into lookup table.
            if disease_record is not None:
                cached_file_path: str = disease_record.file_path
                cached_responses = load_response_from_file(cached_file_path)
            else:
                cached_responses = {}
            
            pmids: List[str]=[]
            mesh_term=get_mesh_term_for_disease(disease.replace("_"," "))
            pmids=search_pubmed(mesh_term)
            print("pmids: ",len(pmids))
            all_literature_details: List[Dict[str,Any]] = fetch_literature_details_in_batches(disease.replace("_"," "),pmids)
            print("all_literature_details: ",len(all_literature_details))
            cached_data[disease.replace("_"," ")] = {"literature": all_literature_details}
            cached_responses[f"{endpoint}"]={"literature": all_literature_details}

            if disease_record is None:
                save_response_to_file(file_path, cached_responses)
                new_record = Disease(id=disease, file_path=file_path)  # Create a new instance of the identified model
                db.add(new_record)  # Add the new record to the session
                db.commit()  # Commit the transaction to save the record to the database
                db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
                # fields)
                print(f"Record with ID {disease} added to the disease table.")
            else:
                save_response_to_file(cached_file_path, cached_responses)

        await set_cached_response(redis, key, cached_data)
        return cached_data

    except Exception as e:
        status_code = getattr(e, "status_code", None)
        if status_code == 429:
            set_rate_limit(RATE_LIMIT)
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evidence/target-mouse-studies/", tags=["Evidence"])
async def get_target_mouse_studies(request: TargetOnlyRequest, redis: Redis = Depends(get_redis),
                            db: Session = Depends(get_db)):
    target: str = request.target.strip().lower()
    key: str = f"/evidence/target-mouse-studies/:{target}"
    endpoint: str = "/evidence/target-mouse-studies/"

    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/target"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    # File path for the JSON response
    file_path: str = os.path.join(cache_dir, f"{target}.json")

    target_record = db.query(Target).filter_by(id=target).first()
    # 1. Check if the cached JSON file exists
    if target_record is not None:
        cached_file_path: str = target_record.file_path
        print(f"Loading cached response from file: {cached_file_path}")
        cached_responses: Dict = load_response_from_file(cached_file_path)

        # Check if the endpoint response exists in the cached data
        if f"{endpoint}" in cached_responses:
            print(f"Returning cached response from file: {cached_file_path}")
            return cached_responses[f"{endpoint}"]

    cached_response_redis = await get_cached_response(redis, key)
    if cached_response_redis:
        print("Returning redis cached response")
        return cached_response_redis

    analyzer = TargetAnalyzer(target)

    try:
        mouse_phenotypes = analyzer.get_mouse_phenotypes()
        mouse_studies = parse_mouse_phenotypes(mouse_phenotypes)
        response = {"mouse_studies": mouse_studies}

        await set_cached_response(redis, key, response)

        if target_record is not None:
            cached_responses = load_response_from_file(cached_file_path)
        else:
            cached_responses = {}

        cached_responses[f"{endpoint}"] = response

        if target_record is None:
            save_response_to_file(file_path, cached_responses)
            new_record = Target(id=target, file_path=file_path)  # Create a new instance of the identified model
            db.add(new_record)  # Add the new record to the session
            db.commit()  # Commit the transaction to save the record to the database
            db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
            # fields)
            print(f"Record with ID {target} added to the target table.")
        else:
            save_response_to_file(cached_file_path, cached_responses)

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evidence/mouse-studies/", tags=["Evidence"])
async def get_mouse_studies(request: DiseasesRequest, redis: Redis = Depends(get_redis),
                            db: Session = Depends(get_db)):
    diseases: List[str] = request.diseases
    diseases = [s.strip().lower().replace(" ", "_") for s in diseases]
    diseases_str = "-".join(diseases)

    # Generate a cache key for the request using target and disease list
    key: str = f"/evidence/mouse-studies/:{diseases_str}"
    endpoint: str = "/evidence/mouse-studies/"

    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/disease"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    cached_diseases: Set[str] = set()
    cached_data: Dict[str,Any] = {}
    for disease in diseases:
        disease_record = db.query(Disease).filter_by(id=f"{disease}").first()
        # 1. Check if the cached JSON file exists
        if disease_record is not None:
            cached_file_path: str = disease_record.file_path
            print(f"Loading cached response from file: {cached_file_path}")
            cached_responses: Dict = load_response_from_file(cached_file_path)

            # Check if the endpoint response exists in the cached data
            if f"{endpoint}" in cached_responses:
                cached_diseases.add(disease)
                print(f"Returning cached response from file: {cached_file_path}")
                cached_data[disease.replace("_"," ")]=cached_responses[f"{endpoint}"]

    # filtering diseases whose response is not present in the json file
    filtered_diseases = [disease for disease in diseases if disease not in cached_diseases]

    if len(filtered_diseases) == 0:  # all disease already present in the json file
        print("All diseases already present in cached json files,returning cached response")
        await set_cached_response(redis, key, cached_data)
        return cached_data

    print("filtered diseases: ", filtered_diseases)
    # Check if cached response exists in Redis
    cached_response_redis: dict = await get_cached_response(redis, key)
    if cached_response_redis:
        print("Returning chached response")
        return cached_response_redis


    try:
        for disease in filtered_diseases:
            disease_record = db.query(Disease).filter_by(id=f"{disease}").first()
            file_path: str = os.path.join(cache_dir, f"{disease}.json")

            # now add the response of each of the disease into lookup table.
            if disease_record is not None:
                cached_file_path: str = disease_record.file_path
                cached_responses = load_response_from_file(cached_file_path)
            else:
                cached_responses = {}
            data=fetch_mouse_model_data_alliancegenome(disease_name=disease.replace("_"," "))
            cached_data[disease.replace("_"," ")]  = {"mouse_studies": data}
            cached_responses[f"{endpoint}"]={"mouse_studies": data}

            if disease_record is None:
                save_response_to_file(file_path, cached_responses)
                new_record = Disease(id=disease, file_path=file_path)  # Create a new instance of the identified model
                db.add(new_record)  # Add the new record to the session
                db.commit()  # Commit the transaction to save the record to the database
                db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
                # fields)
                print(f"Record with ID {disease} added to the disease table.")
            else:
                save_response_to_file(cached_file_path, cached_responses)
        
        await set_cached_response(redis, key, cached_data)
        return cached_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

semaphore = asyncio.Semaphore(1)
@app.post("/evidence/network-biology-semaphore/", tags=["Evidence"])
async def get_network_biology_semaphore(request: DiseasesRequest,
                            db: Session = Depends(get_db)):
    try:
        async with semaphore:  # This will block concurrent requests
            print(f"lock applied and processing {request.diseases}")
            response =  await get_network_biology(request, db)
            print("lock removed")
    except Exception as e:
        raise e
    return response

    
@app.post("/evidence/network-biology/", tags=["Evidence"])
async def get_network_biology(request: DiseasesRequest,
                            db: Session = Depends(get_db)):
    diseases: List[str] = request.diseases
    diseases = [s.strip().lower().replace(" ", "_") for s in diseases]
    diseases_str = "-".join(diseases)
    key: str = f"/evidence/network-biology/:{diseases_str}"
    endpoint: str = "/evidence/network-biology/"

    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/disease"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists
    
    cached_diseases: Set[str] = set()
    cached_data: Dict[str,Any] = {}
    for disease in diseases:
        disease_record = db.query(Disease).filter_by(id=f"{disease}").first()
        # 1. Check if the cached JSON file exists
        if disease_record is not None:
            cached_file_path: str = disease_record.file_path
            print(f"Loading cached response from file: {cached_file_path}")
            cached_responses: Dict = load_response_from_file(cached_file_path)

            # Check if the endpoint response exists in the cached data
            if f"{endpoint}" in cached_responses:
                cached_diseases.add(disease)
                print(f"Returning cached response from file: {cached_file_path}")
                cached_data[disease.replace("_"," ")]=cached_responses[f"{endpoint}"]

        # filtering diseases whose response is not present in the json file
    filtered_diseases = [disease for disease in diseases if disease not in cached_diseases]

    if len(filtered_diseases) == 0:  # all disease already present in the json file
        print("All diseases already present in cached json files,returning cached response")
        cached_data=enrich_disease_pathway_results(cached_data)
        return cached_data

    print("filtered diseases: ", filtered_diseases)

    try:
        for disease in filtered_diseases:
            disease_record = db.query(Disease).filter_by(id=f"{disease}").first()
            file_path: str = os.path.join(cache_dir, f"{disease}.json")

            data=fetch_and_filter_figures_by_disease_and_pmids(disease.replace("_"," "))
            cached_data[disease.replace("_"," ")] = {"results": data}

            if disease_record is not None:
                cached_file_path: str = disease_record.file_path
                cached_responses = load_response_from_file(cached_file_path)
            else:
                cached_responses = {}

            cached_responses[f"{endpoint}"] = {"results": data}

            if disease_record is None:
                save_response_to_file(file_path, cached_responses)
                new_record = Disease(id=disease, file_path=file_path)  # Create a new instance of the identified model
                db.add(new_record)  # Add the new record to the session
                db.commit()  # Commit the transaction to save the record to the database
                db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
                # fields)
                print(f"Record with ID {disease} added to the disease table.")
            else:
                save_response_to_file(cached_file_path, cached_responses)
        cached_data=enrich_disease_pathway_results(cached_data)    
        return cached_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/evidence/search-patent/", tags=["Evidence"])
async def search_patents(request: TargetRequest, redis: Redis = Depends(get_redis),
                         db: Session = Depends(get_db)):
    """
    Return patents for target and diseases.
    """
    target, diseases = validate_target_and_diseases(request, require_diseases=True)
    redis_key: str = generate_cache_key("/evidence/search-patent/", request.target, request.diseases)
    target: str = request.target.strip().lower()
    diseases: List[str] = [d.strip().lower() for d in request.diseases]

    endpoint: str = "/evidence/search-patent/"
    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/target_disease"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists
    cached_diseases: Set[str] = set()
    cached_data: List = []
    for disease in diseases:
        disease = disease.replace(" ", "_")
        target_disease_record = db.query(TargetDisease).filter_by(id=f"{target}-{disease}").first()
        # 1. Check if the cached JSON file exists
        if target_disease_record is not None:
            cached_file_path: str = target_disease_record.file_path
            print(f"Loading cached response from file: {cached_file_path}")
            cached_responses: Dict = load_response_from_file(cached_file_path)

            # Check if the endpoint response exists in the cached data
            if f"{endpoint}" in cached_responses:
                cached_diseases.add(disease.replace("_", " "))
                print(f"Returning cached response from file: {cached_file_path}")
                cached_data.append(cached_responses[f"{endpoint}"]["results"])

    # filtering diseases whose response is not present in the json file
    filtered_diseases = [disease for disease in diseases if disease not in cached_diseases]
    print("filtered_diseases: ", filtered_diseases)
    if len(filtered_diseases) == 0:  # all pairs fo target and disease already present in the json file
        cached_response_json = {"results": cached_data}
        print("All pair of target and disease already present in cached json files,returning cached response")
        await set_cached_response(redis, redis_key, cached_response_json)
        return cached_response_json

    redis_cached_response = await get_cached_response(redis, redis_key)
    if redis_cached_response:
        print("Returning redis cached response")
        return redis_cached_response

    combined_results: List = []
    # Google patents doesn't recognize MeSH terms. Therefore for diseases like AD, we look up the diseases synonyms JSON file.
    # This will ensure we send the correct search term to fetch results from Google patents. 
    # Target terms JSON has a similar purpose. For targets like IL31RA, we need to use variations of this while searching.
    # All these variations are stored in the respective target and disease JSON files.
    
    target_terms_file: str = "../target_data/target_terms.json"
    disease_synonyms_file: str = "../disease_data/diseases_synonyms.json"

    for disease in filtered_diseases:
        # Construct the query for the target and the disease
        query: str = build_query(target, disease, target_terms_file, disease_synonyms_file)
        print(query)

        # Define the parameters for the API request
        params = {
            "engine": "google_patents",
            "q": query,
            "api_key": SERP_API_KEY,
            "language": "ENGLISH",
            "num": 100
        }
        disease_key: str = disease.replace(" ", "_")

        try:
            # Make the API request
            response = requests.get(SERP_API_URL, params=params)
            response.raise_for_status()  # Will raise an error for bad responses
            data = response.json()

            # Keys you want to extract
            keys_to_extract: List[str] = ["patent_id", "pdf", "title", "assignee", "filing_date", "grant_date"]

            # Process each entry in data["organic_results"]
            filtered_results: List[Dict[str, Any]] = []

            for entry in data.get("organic_results", []):
                # Extract specific key values from each dictionary, defaulting to empty string if key is missing
                filtered_data: Dict[str, Any] = {key: entry.get(key, "") for key in keys_to_extract}

                # Extract the country_status separately, handling the dictionary type
                country_status: Dict[str, Any] = entry.get("country_status", {})

                # Add country_status to the filtered_data dictionary
                filtered_data["country_status"] = country_status

                # Calculate the expiry_date using filing_date if available, else set it to empty string
                filtered_data["expiry_date"] = add_years(filtered_data["filing_date"], 20) if filtered_data[
                    "filing_date"] else ""

                # Append the processed data to the filtered_results list
                filtered_results.append(filtered_data)

            # Append the JSON response for the current disease
            combined_results.append({"target": target, "disease": disease, "results": filtered_results})

            target_disease_record = db.query(TargetDisease).filter_by(id=f"{target}-{disease_key}").first()
            file_path: str = os.path.join(cache_dir, f"{target}-{disease_key}.json")

            # now add the response of each of the disease into lookup table.
            if target_disease_record is not None:
                cached_file_path: str = target_disease_record.file_path
                cached_responses = load_response_from_file(cached_file_path)
            else:
                cached_responses = {}

            cached_responses[f"{endpoint}"] = {"results": {
                "target": target,
                "disease": disease,
                "results": filtered_results
            }}

            if target_disease_record is None:
                save_response_to_file(file_path, cached_responses)
                new_record = TargetDisease(id=f"{target}-{disease_key}",
                                           file_path=file_path)  # Create a new instance of the identified model
                db.add(new_record)  # Add the new record to the session
                db.commit()  # Commit the transaction to save the record to the database
                db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
                # fields)
                print(f"Record with ID {target}-{disease} added to the target_disease table.")
            else:
                save_response_to_file(cached_file_path, cached_responses)


        except requests.RequestException as exc:
            # Raise an HTTP exception if the request fails
            raise HTTPException(status_code=exc.response.status_code, detail=f"Error: {exc.response.text}")

    combined_results.extend(cached_data)
    final_response = {"results": combined_results}
    await set_cached_response(redis, redis_key, final_response)
    return final_response


@app.post("/evidence/functional-genomics/", tags=["Evidence"])
async def get_functional_genomics(request: TargetOnlyRequest, redis: Redis = Depends(get_redis),
                                  db: Session = Depends(get_db)):
    """
    Return functional genomics for a given target.
    """
    target: str = request.target.strip().lower()
    print(target)
    key: str = f"/evidence/functional-genomics/:{target}"
    endpoint: str = "/evidence/functional-genomics/"

    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/target"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    # File path for the JSON response
    file_path: str = os.path.join(cache_dir, f"{target}.json")

    target_record = db.query(Target).filter_by(id=target).first()
    # 1. Check if the cached JSON file exists
    if target_record is not None:
        cached_file_path: str = target_record.file_path
        print(f"Loading cached response from file: {cached_file_path}")
        cached_responses: Dict = load_response_from_file(cached_file_path)

        # Check if the endpoint response exists in the cached data
        if f"{endpoint}" in cached_responses:
            print(f"Returning cached response from file: {cached_file_path}")
            return cached_responses[f"{endpoint}"]

    cached_response_redis = await get_cached_response(redis, key)
    if cached_response_redis:
        print("Returning redis cached response")
        return cached_response_redis

    try:

        response: Dict[str, List[Dict[str, Any]]] = {"results": find_matching_screens_for_target(target)}

        await set_cached_response(redis, key, response)

        if target_record is not None:
            cached_responses = load_response_from_file(cached_file_path)
        else:
            cached_responses = {}

        cached_responses[f"{endpoint}"] = response

        if target_record is None:
            save_response_to_file(file_path, cached_responses)
            new_record = Target(id=target, file_path=file_path)  # Create a new instance of the identified model
            db.add(new_record)  # Add the new record to the session
            db.commit()  # Commit the transaction to save the record to the database
            db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
            # fields)
            print(f"Record with ID {target} added to the target table.")
        else:
            save_response_to_file(cached_file_path, cached_responses)

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

semaphore = asyncio.Semaphore(1)
@app.post("/evidence/rna-sequence-semaphore/", tags=["Evidence"])
async def get_rna_sequence_semaphore(
        request: DiseasesRequest,  # Pydantic model that contains the target and diseases list
        redis: Redis = Depends(get_redis),  # Redis dependency for caching
        db: Session = Depends(get_db)
):
    try:
        async with semaphore:  # This will block concurrent requests
            print(f"lock applied and processing {request.diseases}")
            response =  await get_rna_sequence(request, redis, db)
            print("lock removed")
    except Exception as e:
        raise e
    return response

@app.post("/evidence/rna-sequence/", tags=["Evidence"])
async def get_rna_sequence(
        request: DiseasesRequest,  # Pydantic model that contains the target and diseases list
        redis: Redis = Depends(get_redis),  # Redis dependency for caching
        db: Session = Depends(get_db)
):
    """
    Fetches RNA sequence data for list of diseases.
    """
    diseases: List[str] = request.diseases
    diseases = [s.strip().lower().replace(" ", "_") for s in diseases]
    diseases_str = "-".join(diseases)

    # Generate a cache key for the request using target and disease list
    key: str = f"/evidence/rna-sequence/:{diseases_str}"
    endpoint: str = "/evidence/rna-sequence/"

    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/disease"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    cached_diseases: Set[str] = set()
    cached_data: dict = {}
    for disease in diseases:
        disease_record = db.query(Disease).filter_by(id=f"{disease}").first()
        # 1. Check if the cached JSON file exists
        if disease_record is not None:
            cached_file_path: str = disease_record.file_path
            print(f"Loading cached response from file: {cached_file_path}")
            cached_responses: Dict = load_response_from_file(cached_file_path)

            # Check if the endpoint response exists in the cached data
            disease_name: str = disease.replace("_", " ")
            if f"{endpoint}" in cached_responses and disease_name in cached_responses[endpoint]:
                cached_diseases.add(disease)
                print(f"Returning cached response from file: {cached_file_path}")
                cached_data[disease_name] = cached_responses[endpoint][disease_name]

    # filtering diseases whose response is not present in the json file
    filtered_diseases = [disease for disease in diseases if disease not in cached_diseases]
    filtered_diseases = [disease.replace("_", " ") for disease in filtered_diseases]

    if len(filtered_diseases) == 0:  # all disease already present in the json file
        print("All diseases already present in cached json files,returning cached response")
        await set_cached_response(redis, key, cached_data)
        return cached_data

    print("filtered diseases: ", filtered_diseases)
    # Check if cached response exists in Redis
    cached_response_redis: dict = await get_cached_response(redis, key)
    if cached_response_redis:
        print("Returning chached response")
        return cached_response_redis

    try:
        if is_rate_limited():
            remaining_time = int(rate_limited_until - time.time())
            raise HTTPException(status_code=429, detail=f"Rate limit in effect. Try again after {remaining_time} seconds.")
    
        response: dict = get_geo_data_for_diseases(filtered_diseases)
        response=add_platform_name(response)
        response=add_study_type(response)

        for disease, value in response.items():
            disease_key: str = disease.strip().lower().replace(" ", "_")
            disease_record = db.query(Disease).filter_by(id=f"{disease_key}").first()
            file_path: str = os.path.join(cache_dir, f"{disease_key}.json")

            # now add the response of each of the disease into lookup table.
            if disease_record is not None:
                cached_file_path: str = disease_record.file_path
                cached_responses = load_response_from_file(cached_file_path)
            else:
                cached_responses = {}

            cached_responses[f"{endpoint}"] = {disease: value}

            if disease_record is None:
                save_response_to_file(file_path, cached_responses)
                new_record = Disease(id=f"{disease_key}",
                                     file_path=file_path)  # Create a new instance of the identified model
                db.add(new_record)  # Add the new record to the session
                db.commit()  # Commit the transaction to save the record to the database
                db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
                # fields)
                print(f"Record with ID {disease} added to the disease table.")
            else:
                save_response_to_file(cached_file_path, cached_responses)
        response.update(cached_data)
        await set_cached_response(redis, key, response)

        # Return the JSON response from the API
        return response

    except Exception as e:
        status_code = getattr(e, "status_code", None)
        if status_code == 429:
            set_rate_limit(RATE_LIMIT)
            raise e
        # Raise a 500 HTTPException if an error occurs during the request
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/evidence/top-10-literature/", tags=["Evidence"])
async def get_top_10_literature(request: DiseasesRequest):
    """
    Fetch disease information from the loaded JSON data.
    Args:
        request (DiseaseRequest): A diseases to fetch data for.

    Returns:
        Dict: Disease information if available, or error message if not found.
    """
    diseases: str = [disease.strip().lower() for disease in request.diseases]
    # Initialize a dictionary to hold the response
    result: Dict[str, Any] = {}
    try: 
        for disease in diseases:
            result[disease] = get_top_10_literature_helper(disease)

        return result
    except Exception as e:
        # Raise a 500 HTTPException if an error occurs during the request
        raise HTTPException(status_code=500, detail=str(e))
    
#################################### Genomics Data ##############################################
@app.post("/genomics/pgscatalog", tags=["Genomics"])
async def pgs_catalog_data(request: DiseasesRequest, redis: Redis = Depends(get_redis),
                            db: Session = Depends(get_db)):
    
    """
    Fetches Genomics Data for given diseases using PGSCatalog API.
    """
    diseases: List[str] = request.diseases
    diseases = [s.strip().lower().replace(" ", "_") for s in diseases]
    diseases_str = "-".join(diseases)

    # Generate a cache key for the request using target and disease list
    key: str = f"/genomics/pgscatalog:{diseases_str}"
    endpoint: str = "/genomics/pgscatalog/"

    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/disease"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    cached_diseases: Set[str] = set()
    cached_data: List = []
    response = {}
    for disease in diseases:
        disease_record = db.query(Disease).filter_by(id=f"{disease}").first()
        # 1. Check if the cached JSON file exists
        if disease_record is not None:
            cached_file_path: str = disease_record.file_path
            print(f"Loading cached response from file: {cached_file_path}")
            cached_responses: Dict = load_response_from_file(cached_file_path)

            # Check if the endpoint response exists in the cached data
            if f"{endpoint}" in cached_responses:
                cached_diseases.add(disease)
                print(f"Returning cached response from file: {cached_file_path}")
                response[disease.replace('_', ' ')] = cached_responses[endpoint]

    # filtering diseases whose response is not present in the json file
    filtered_diseases = [disease for disease in diseases if disease not in cached_diseases]

    if len(filtered_diseases) == 0:  # all disease already present in the json file
        print("All diseases already present in cached json files,returning cached response")
        await set_cached_response(redis, key, response)
        return response

    print("filtered diseases: ", filtered_diseases)
    # Check if cached response exists in Redis
    cached_response_redis: dict = await get_cached_response(redis, key)
    if cached_response_redis:
        print("Returning chached response")
        return cached_response_redis

    try:
        
        diseases_and_efo: Dict[str, str] = {}  # Dictionary to store disease names and their corresponding EFO IDs

        for disease in filtered_diseases:
            disease_name: str = disease.strip().lower().replace(" ", "_")
            disease_record = db.query(Disease).filter_by(id=f"{disease_name}").first()
            file_path: str = os.path.join(cache_dir, f"{disease_name}.json")

            # now add the response of each of the disease into lookup table.
            if disease_record is not None:
                cached_file_path: str = disease_record.file_path
                cached_responses = load_response_from_file(cached_file_path)
            else:
                cached_responses = {}
            
            # Fetch PGS CAtalog data using EFO IDs
            efo_id: str = get_efo_id(disease_name.replace('_', ' ').lower())
            if efo_id:
                diseases_and_efo[disease_name] = efo_id.replace(':', '_')
                genomics_data = fetch_pgs_data(efo_id)
            else:
                genomics_data = [f"EFO ID not found for {disease_name.replace('_', ' ')}"]

            cached_responses[f"{endpoint}"] = genomics_data
            if disease_record is None:
                save_response_to_file(file_path, cached_responses)
                new_record = Disease(id=f"{disease}",
                                     file_path=file_path)  # Create a new instance of the identified model
                db.add(new_record)  # Add the new record to the session
                db.commit()  # Commit the transaction to save the record to the database
                db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
                # fields)
                print(f"Record with ID {disease} added to the disease table.")
            else:
                save_response_to_file(cached_file_path, cached_responses)
            print('disease: ', disease)
            print("output: ", cached_responses[f"{endpoint}"])
            response[disease.replace('_', ' ')]=cached_responses[f"{endpoint}"]
        await set_cached_response(redis, key, response)

        # Return the JSON response from the API
        return response

    except Exception as e:
        # Raise a 500 HTTPException if an error occurs during the request
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/genomics/gwas-studies", tags=["Genomics"])
async def gwas_studies_data(request: DiseasesRequest, redis: Redis = Depends(get_redis),
                            db: Session = Depends(get_db)):
    
    """
    Fetches Studies from GWAS for given diseases using GWAS API.
    """
    diseases: List[str] = request.diseases
    diseases = [s.strip().lower().replace(" ", "_") for s in diseases]
    diseases_str = "-".join(diseases)

    # Generate a cache key for the request using target and disease list
    key: str = f"/genomics/gwas-studies:{diseases_str}"
    endpoint: str = "/genomics/gwas-studies/"

    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/disease"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    cached_diseases: Set[str] = set()
    cached_data: List = []
    response = {}
    for disease in diseases:
        disease_record = db.query(Disease).filter_by(id=f"{disease}").first()
        # 1. Check if the cached JSON file exists
        if disease_record is not None:
            cached_file_path: str = disease_record.file_path
            print(f"Loading cached response from file: {cached_file_path}")
            cached_responses: Dict = load_response_from_file(cached_file_path)

            # Check if the endpoint response exists in the cached data
            if f"{endpoint}" in cached_responses:
                cached_diseases.add(disease)
                print(f"Returning cached response from file: {cached_file_path}")
                response[disease] = cached_responses[endpoint]

    # filtering diseases whose response is not present in the json file
    filtered_diseases = [disease for disease in diseases if disease not in cached_diseases]

    if len(filtered_diseases) == 0:  # all disease already present in the json file
        print("All diseases already present in cached json files,returning cached response")
        await set_cached_response(redis, key, response)
        return response

    print("filtered diseases: ", filtered_diseases)
    # Check if cached response exists in Redis
    cached_response_redis: dict = await get_cached_response(redis, key)
    if cached_response_redis:
        print("Returning chached response")
        return cached_response_redis

    try:
        
        diseases_and_efo: Dict[str, str] = {}  # Dictionary to store disease names and their corresponding EFO IDs

        for disease in filtered_diseases:
            disease_name: str = disease.strip().lower().replace(" ", "_")
            disease_record = db.query(Disease).filter_by(id=f"{disease_name}").first()
            file_path: str = os.path.join(cache_dir, f"{disease_name}.json")

            # now add the response of each of the disease into lookup table.
            if disease_record is not None:
                cached_file_path: str = disease_record.file_path
                cached_responses = load_response_from_file(cached_file_path)
            else:
                cached_responses = {}
            
            # Fetch PGS CAtalog data using EFO IDs
            efo_id: str = get_efo_id(disease_name.replace('_', ' ').lower())
            if efo_id:
                diseases_and_efo[disease_name] = efo_id.replace(':', '_')
                genomics_data = get_gwas_studies(efo_id)
            else:
                genomics_data = [f"EFO ID not found for {disease_name.replace('_', ' ')}"]

            cached_responses[f"{endpoint}"] = genomics_data
            if disease_record is None:
                save_response_to_file(file_path, cached_responses)
                new_record = Disease(id=f"{disease}",
                                     file_path=file_path)  # Create a new instance of the identified model
                db.add(new_record)  # Add the new record to the session
                db.commit()  # Commit the transaction to save the record to the database
                db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
                # fields)
                print(f"Record with ID {disease} added to the disease table.")
            else:
                save_response_to_file(cached_file_path, cached_responses)
            print('disease: ', disease)
            print("output: ", cached_responses[f"{endpoint}"])
            response[disease]=cached_responses[f"{endpoint}"]
        await set_cached_response(redis, key, response)

        # Return the JSON response from the API
        return response

    except Exception as e:
        # Raise a 500 HTTPException if an error occurs during the request
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/genomics/locus-zoom", tags=["Genomics"])
async def plot_locus_zoom(request: DiseasesRequest, redis: Redis = Depends(get_redis),
                            db: Session = Depends(get_db)):
    try:
        diseases: str = [disease.lower() for disease in request.diseases]
        response = {}
        for disease in diseases:
            print('disease: ', disease)
            efo_id: str = get_efo_id(disease)
            gwas_disease_file_path = os.path.join(GWAS_DATA_DIR, f'{efo_id}.tsv')
            print("gwas_disease_file_path: ", gwas_disease_file_path)
            if not os.path.exists(gwas_disease_file_path):
                print("path doesn't exists")
                gwas_disease_file_path = load_data(efo_id)
            print("gwas_disease_file_path: ", gwas_disease_file_path)
            if gwas_disease_file_path and os.path.isfile(gwas_disease_file_path):
                response[disease] = gwas_disease_file_path
            
            else:
                response[disease] = None
            print("response: ", response)
        return response

    except Exception as e:
        return None
#################################### target assessment page ##############################################

@app.post("/target-assessment/targetability/", tags=["Target Assessment"])
async def get_targetability(request: TargetOnlyRequest, redis: Redis = Depends(get_redis),
                            db: Session = Depends(get_db)):
    target: str = request.target.strip().lower()
    key: str = f"/target-assessment/targetability/:{target}"
    endpoint: str = "/target-assessment/targetability/"

    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/target"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    # File path for the JSON response
    file_path: str = os.path.join(cache_dir, f"{target}.json")

    target_record = db.query(Target).filter_by(id=target).first()
    # 1. Check if the cached JSON file exists
    if target_record is not None:
        cached_file_path: str = target_record.file_path
        print(f"Loading cached response from file: {cached_file_path}")
        cached_responses: Dict = load_response_from_file(cached_file_path)

        # Check if the endpoint response exists in the cached data
        if f"{endpoint}" in cached_responses:
            print(f"Returning cached response from file: {cached_file_path}")
            return cached_responses[f"{endpoint}"]

    cached_response_redis = await get_cached_response(redis, key)
    if cached_response_redis:
        print("Returning redis cached response")
        return cached_response_redis

    analyzer = TargetAnalyzer(target)

    try:
        targetability_data = analyzer.get_targetablitiy()
        print("targetability_data: ", targetability_data)
        parsed_targetability = parse_targetability(targetability_data, target)
        response = {"targetability": parsed_targetability}

        await set_cached_response(redis, key, response)

        if target_record is not None:
            cached_responses = load_response_from_file(cached_file_path)
        else:
            cached_responses = {}

        cached_responses[f"{endpoint}"] = response

        if target_record is None:
            save_response_to_file(file_path, cached_responses)
            new_record = Target(id=target, file_path=file_path)  # Create a new instance of the identified model
            db.add(new_record)  # Add the new record to the session
            db.commit()  # Commit the transaction to save the record to the database
            db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
            # fields)
            print(f"Record with ID {target} added to the target table.")
        else:
            save_response_to_file(cached_file_path, cached_responses)

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/target-assessment/geneEssentialityMap/", tags=["Target Assessment"])
async def get_gene_essentiality_map(request: TargetOnlyRequest, redis: Redis = Depends(get_redis),
                                    db: Session = Depends(get_db)):
    target: str = request.target.strip().lower()
    key: str = f"/target-assessment/geneEssentialityMap/:{target}"
    endpoint: str = "/target-assessment/geneEssentialityMap/"
    print(f"gene map {target}")
    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/target"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    # File path for the JSON response
    file_path: str = os.path.join(cache_dir, f"{target}.json")

    target_record = db.query(Target).filter_by(id=target).first()
    # 1. Check if the cached JSON file exists
    if target_record is not None:
        cached_file_path: str = target_record.file_path
        print(f"Loading cached response from file: {cached_file_path}")
        cached_responses: Dict = load_response_from_file(cached_file_path)

        # Check if the endpoint response exists in the cached data
        if f"{endpoint}" in cached_responses:
            print(f"Returning cached response from file: {cached_file_path}")
            return cached_responses[f"{endpoint}"]

    cached_response_redis = await get_cached_response(redis, key)
    if cached_response_redis:
        print("Returning redis cached response")
        return cached_response_redis

    analyzer = TargetAnalyzer(target)

    try:
        print("Getting gene essentiality data")
        geneEssentialityMapData = analyzer.get_target_gene_map()
        print("geneEssentialityMap ", geneEssentialityMapData)
        parsed_targetability = parse_gene_map(geneEssentialityMapData)
        response = {"geneEssentialityMap": parsed_targetability}

        await set_cached_response(redis, key, response)

        if target_record is not None:
            cached_responses = load_response_from_file(cached_file_path)
        else:
            cached_responses = {}

        cached_responses[f"{endpoint}"] = response

        if target_record is None:
            save_response_to_file(file_path, cached_responses)
            new_record = Target(id=target, file_path=file_path)  # Create a new instance of the identified model
            db.add(new_record)  # Add the new record to the session
            db.commit()  # Commit the transaction to save the record to the database
            db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
            # fields)
            print(f"Record with ID {target} added to the target table.")
        else:
            save_response_to_file(cached_file_path, cached_responses)

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/target-assessment/tractability/", tags=["Target Assessment"])
async def get_tractability(request: TargetOnlyRequest, redis: Redis = Depends(get_redis),
                           db: Session = Depends(get_db)):
    target: str = request.target.strip().lower()
    key: str = f"/target-assessment/tractability/:{target}"
    endpoint: str = "/target-assessment/tractability/"

    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/target"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    # File path for the JSON response
    file_path: str = os.path.join(cache_dir, f"{target}.json")

    target_record = db.query(Target).filter_by(id=target).first()
    # 1. Check if the cached JSON file exists
    if target_record is not None:
        cached_file_path: str = target_record.file_path
        print(f"Loading cached response from file: {cached_file_path}")
        cached_responses: Dict = load_response_from_file(cached_file_path)

        # Check if the endpoint response exists in the cached data
        if f"{endpoint}" in cached_responses:
            print(f"Returning cached response from file: {cached_file_path}")
            return cached_responses[f"{endpoint}"]

    cached_response_redis = await get_cached_response(redis, key)
    if cached_response_redis:
        print("Returning redis cached response")
        return cached_response_redis

    analyzer = TargetAnalyzer(target)

    try:
        tractability_data = analyzer.get_tractability()
        parsed_tractability = parse_tractability(tractability_data)
        response = {"tractability": parsed_tractability}

        await set_cached_response(redis, key, response)

        if target_record is not None:
            cached_responses = load_response_from_file(cached_file_path)
        else:
            cached_responses = {}

        cached_responses[f"{endpoint}"] = response

        if target_record is None:
            save_response_to_file(file_path, cached_responses)
            new_record = Target(id=target, file_path=file_path)  # Create a new instance of the identified model
            db.add(new_record)  # Add the new record to the session
            db.commit()  # Commit the transaction to save the record to the database
            db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
            # fields)
            print(f"Record with ID {target} added to the target table.")
        else:
            save_response_to_file(cached_file_path, cached_responses)

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/target-assessment/paralogs/", tags=["Target Assessment"])
async def get_paralogs(request: TargetOnlyRequest, redis: Redis = Depends(get_redis), db: Session = Depends(get_db)):
    target: str = request.target.strip().lower()
    key: str = f"/target-assessment/paralogs/:{target}"
    endpoint: str = "/target-assessment/paralogs/"

    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/target"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    # File path for the JSON response
    file_path: str = os.path.join(cache_dir, f"{target}.json")

    target_record = db.query(Target).filter_by(id=target).first()
    # 1. Check if the cached JSON file exists
    if target_record is not None:
        cached_file_path: str = target_record.file_path
        print(f"Loading cached response from file: {cached_file_path}")
        cached_responses: Dict = load_response_from_file(cached_file_path)

        # Check if the endpoint response exists in the cached data
        if f"{endpoint}" in cached_responses:
            print(f"Returning cached response from file: {cached_file_path}")
            return cached_responses[f"{endpoint}"]

    cached_response_redis = await get_cached_response(redis, key)
    if cached_response_redis:
        print("Returning redis cached response")
        return cached_response_redis

    analyzer = TargetAnalyzer(target)

    try:
        paralogs_data = analyzer.get_paralogs()
        parsed_paralogs = parse_paralogs(paralogs_data)
        response = {"paralogs": parsed_paralogs}
        await set_cached_response(redis, key, response)

        if target_record is not None:
            cached_responses = load_response_from_file(cached_file_path)
        else:
            cached_responses = {}

        cached_responses[f"{endpoint}"] = response

        if target_record is None:
            save_response_to_file(file_path, cached_responses)
            new_record = Target(id=target, file_path=file_path)  # Create a new instance of the identified model
            db.add(new_record)  # Add the new record to the session
            db.commit()  # Commit the transaction to save the record to the database
            db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
            # fields)
            print(f"Record with ID {target} added to the target table.")
        else:
            save_response_to_file(cached_file_path, cached_responses)

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fetch-graph/")
async def fetch_graph(request: GraphRequest, driver=Depends(get_neo4j_driver)
                      , db: Session = Depends(get_db)
                      ):
    """
    Return the data for knowledge graph.
    """

    efo_id_list: List[str] = list(map(get_efo_id, request.target_diseases))
    key_list: List[str] = [request.target_gene.strip().lower()] + efo_id_list + [request.metapath]
    key: str = ":".join(sorted(key_list))
    endpoint: str = "/fetch-graph/"
    print(key)
    cache_dir: str = "cached_data_json/target_disease"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    file_path: str = os.path.join(cache_dir, f"{key}.json")

    target_disease_record = db.query(TargetDisease).filter_by(id=f"{key}").first()
    # 1. Check if the cached JSON file exists
    if target_disease_record is not None:
        cached_file_path: str = target_disease_record.file_path
        print(f"Loading cached response from file: {cached_file_path}")
        cached_responses: Dict = load_response_from_file(cached_file_path)
        print(f"Returning cached response from file: {cached_file_path}")
        return cached_responses

    QUERIES = {
        "DGPG": """
            MATCH (d:`biolink:Disease`)-[r1]-(g1:`biolink:Gene`)-[r2]-(bp:`biolink:Pathway`)-[r3]-(g:`biolink:Gene`)
            WHERE g.name = $target_gene
            AND (d.id IN $diseases 
            OR any(id in d.equivalent_identifiers WHERE id IN $diseases))
            RETURN d, r1, g1, r2, bp, r3, g
        """,
        "GGGD": """
            MATCH(g:`biolink:Gene`{name:"TNFRSF4"})-[r1]-(g2:`biolink:Gene`)-[r2:`biolink:directly_physically_interacts_with`]-(g3)-[r3:`biolink:target_for`]-(d:`biolink:Disease`{name:"dermatitis, atopic"})
            WHERE g.name = $target_gene
            AND (d.id IN $diseases 
            OR any(id in d.equivalent_identifiers WHERE id IN $diseases))
            RETURN g, r1, g2, r2, g3, r3, d
        """
    }

    NODE_TYPES = {
        "DGPG": ['d', 'g1', 'bp', 'g'],
        "GGGD": ['g', 'g2', 'g3', 'd']
    }

    EDGE_TYPES = {
        "DGPG": ['r1', 'r2', 'r3'],
        "GGGD": ['r1', 'r2', 'r3']
    }

    # TODO: Add exception handling and return appropriate response and status code

    with driver.session() as session:
        result = session.run(
            QUERIES[request.metapath],
            parameters={
                "target_gene": request.target_gene,
                "diseases": efo_id_list
            }
        )

        # Format the results for Cytoscape.js
        graph_elements = format_for_cytoscape(
            query_result=result,
            node_types=NODE_TYPES[request.metapath],
            edge_types=EDGE_TYPES[request.metapath]
        )
    response: Dict[str, Any] = {"elements": graph_elements}

    if target_disease_record is None:
        save_big_response_to_file(file_path, response)
        new_record = TargetDisease(id=key, file_path=file_path)  # Create a new instance of the identified model
        db.add(new_record)  # Add the new record to the session
        db.commit()  # Commit the transaction to save the record to the database
        db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
        # fields)
        print(f"Record with ID {key} added to the target-disease table.")

    return response


"""
GraphRAG Service Below
"""


class QuestionRequest(BaseModel):
    question: str


class AnswerResponse(BaseModel):
    answer: str
    llm_calls: int
    prompt_tokens: int


@app.post("/graphrag-answer/", response_model=AnswerResponse)
def graphrag_answer(question_request: QuestionRequest):
    try:
        # invoke graphrag for answer
        answer, llm_calls, prompt_tokens = get_graphrag_answer(question_request.question)

        # replacing references with clickable spans
        def format_references(answer_text):
            import re
            # regex matches patterns like Reports (15, 12, 27)
            return re.sub(r'Reports \(([\d, ,]+)(?:, \+more)?\)', lambda match: 'Reports ' + ', '.join(
                [f'<span onClick={{handleRef}} class="reference" data-ref="{num.strip()}">{num.strip()}</span>' for num
                 in match.group(1).split(',')]) + (', +more' if '+more' in match.group(0) else ''), answer_text)

        formatted_answer = format_references(answer)

        return AnswerResponse(
            answer=formatted_answer,
            llm_calls=llm_calls,
            prompt_tokens=prompt_tokens
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/fetch-chunk/{reference_id}")
def fetch_chunk(reference_id: int):
    graphrag_dir = getenv("GRAPHRAG_DATA_DIR", None)
    try:
        communities_path = graphrag_dir + "/create_final_communities.parquet"
        text_units_path = graphrag_dir + "/create_base_text_units.parquet"

        result = fetch_text_chunks(reference_id, communities_path, text_units_path, folder_path="/app/graphRAG/data")

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#################################### disease profile page ##############################################


@app.post("/disease-profile/details/", tags=["Disease Profile"])
async def get_diseases_profiles(
        request: DiseasesRequest,  # Pydantic model that contains the target and diseases list
        redis: Redis = Depends(get_redis),  # Redis dependency for caching
        db: Session = Depends(get_db)
):
    """
    Fetches disease profiles including their description and synonyms from the OpenTargets API.
    """
    diseases: List[str] = request.diseases
    diseases = [s.strip().lower().replace(" ", "_") for s in diseases]
    diseases_str = "-".join(diseases)

    # Generate a cache key for the request using target and disease list
    key: str = f"/disease-profile/details:{diseases_str}"
    endpoint: str = "/disease-profile/details/"

    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/disease"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    cached_diseases: Set[str] = set()
    cached_data: List = []
    for disease in diseases:
        disease_record = db.query(Disease).filter_by(id=f"{disease}").first()
        # 1. Check if the cached JSON file exists
        if disease_record is not None:
            cached_file_path: str = disease_record.file_path
            print(f"Loading cached response from file: {cached_file_path}")
            cached_responses: Dict = load_response_from_file(cached_file_path)

            # Check if the endpoint response exists in the cached data
            if f"{endpoint}" in cached_responses:
                cached_diseases.add(disease)
                print(f"Returning cached response from file: {cached_file_path}")
                cached_data.append(cached_responses[f"{endpoint}"]["data"]["diseases"])

    # filtering diseases whose response is not present in the json file
    filtered_diseases = [disease for disease in diseases if disease not in cached_diseases]

    if len(filtered_diseases) == 0:  # all disease already present in the json file
        response = {"data": {"diseases": cached_data}}
        print("All diseases already present in cached json files,returning cached response")
        await set_cached_response(redis, key, response)
        return response

    print("filtered diseases: ", filtered_diseases)
    # Check if cached response exists in Redis
    cached_response_redis: dict = await get_cached_response(redis, key)
    if cached_response_redis:
        print("Returning chached response")
        return cached_response_redis

    diseases_and_efo: Dict[str, str] = {}  # Dictionary to store disease names and their corresponding EFO IDs

    # Iterate through each disease, fetch its EFO ID, and store it in the dictionary
    for disease_name in filtered_diseases:
        efo_id: str = get_efo_id(disease_name.replace("_", " "))
        if efo_id:
            diseases_and_efo[disease_name] = efo_id.replace(':', '_')
        else:
            raise HTTPException(status_code=404, detail=f"EFO ID not found for {disease_name}")

    # Extract the list of EFO IDs from the diseases_and_efo dictionary
    diseases_efo_ids: List[str] = list(diseases_and_efo.values())

    # GraphQL query string for fetching disease details
    query_string: str = DiseaseAnnotationQueryVariables

    # Set the variables to be passed into the GraphQL query
    variables: Dict[str, List[str]] = {"efoIds": diseases_efo_ids}
    print(variables)
    try:
        # Define the base URL for the OpenTargets API
        base_url: str = "https://api.platform.opentargets.org/api/v4/graphql"

        # Make a POST request to the GraphQL API
        response = requests.post(base_url, json={"query": query_string, "variables": variables})
        response = response.json()
        print("response: ", response)
        
        for record in response["data"]["diseases"]:
            disease: str = record["name"].strip().lower()
            strapi_disease_description: str=get_disease_description_strapi(disease)
            if strapi_disease_description:
                record["description"]=strapi_disease_description

        for record in response["data"]["diseases"]:
            disease: str = record["name"].strip().lower().replace(" ", "_")
            disease_record = db.query(Disease).filter_by(id=f"{disease}").first()
            file_path: str = os.path.join(cache_dir, f"{disease}.json")

            # now add the response of each of the disease into lookup table.
            if disease_record is not None:
                cached_file_path: str = disease_record.file_path
                cached_responses = load_response_from_file(cached_file_path)
            else:
                cached_responses = {}

            cached_responses[f"{endpoint}"] = {"data": {"diseases": record}}

            if disease_record is None:
                save_response_to_file(file_path, cached_responses)
                new_record = Disease(id=f"{disease}",
                                     file_path=file_path)  # Create a new instance of the identified model
                db.add(new_record)  # Add the new record to the session
                db.commit()  # Commit the transaction to save the record to the database
                db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
                # fields)
                print(f"Record with ID {disease} added to the disease table.")
            else:
                save_response_to_file(cached_file_path, cached_responses)

        response["data"]["diseases"].extend(cached_data)
        await set_cached_response(redis, key, response)

        # Return the JSON response from the API
        return response

    except Exception as e:
        # Raise a 500 HTTPException if an error occurs during the request
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/disease-profile/details-llm/", tags=["Disease Profile"])
async def get_diseases_profiles_llm(
    request: DiseasesRequest,
    redis: Redis = Depends(get_redis),
    db: Session = Depends(get_db)
):
    """
    Fetches disease profiles using LLM with caching support.
    """
    diseases: List[str] = request.diseases
    diseases = [s.strip().lower().replace(" ", "_") for s in diseases]
    diseases_str = "-".join(diseases)

    # Generate cache key
    key: str = f"/disease-profile/details-llm/:{diseases_str}"
    endpoint: str = "/disease-profile/details-llm/"

    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/disease"
    os.makedirs(cache_dir, exist_ok=True)

    # Check cache in files and database
    cached_diseases: Set[str] = set()
    cached_data: Dict[str, Any] = {}
    
    for disease in diseases:
        disease_record = db.query(Disease).filter_by(id=f"{disease}").first()
        if disease_record is not None:
            cached_file_path: str = disease_record.file_path
            print(f"Loading cached response from file: {cached_file_path}")
            cached_responses: Dict = load_response_from_file(cached_file_path)

            if f"{endpoint}" in cached_responses:
                cached_diseases.add(disease)
                print(f"Returning cached response from file: {cached_file_path}")
                cached_data[disease.replace("_", " ")] = cached_responses[f"{endpoint}"]

    # Filter diseases not in cache
    filtered_diseases = [disease for disease in diseases if disease not in cached_diseases]

    if len(filtered_diseases) == 0:
        print("All diseases already present in cached json files, returning cached response")
        await set_cached_response(redis, key, cached_data)
        return cached_data

    print("filtered diseases: ", filtered_diseases)

    # Check Redis cache
    cached_response_redis = await get_cached_response(redis, key)
    if cached_response_redis:
        print("Returning redis cached response")
        return cached_response_redis

    try:
        # Process non-cached diseases
        for disease in filtered_diseases:
            disease_record = db.query(Disease).filter_by(id=f"{disease}").first()
            file_path: str = os.path.join(cache_dir, f"{disease}.json")

            if disease_record is not None:
                cached_file_path: str = disease_record.file_path
                cached_responses = load_response_from_file(cached_file_path)
            else:
                cached_responses = {}

            # Get LLM interpretation for disease
            disease_data = disease_interpreter(disease_name=disease.replace("_", " "))
            cached_data[disease.replace("_", " ")] = disease_data
            cached_responses[f"{endpoint}"] = disease_data

            # Save to cache file and database
            if disease_record is None:
                save_response_to_file(file_path, cached_responses)
                new_record = Disease(id=disease, file_path=file_path)
                db.add(new_record)
                db.commit()
                db.refresh(new_record)
                print(f"Record with ID {disease} added to the disease table.")
            else:
                save_response_to_file(cached_file_path, cached_responses)

        await set_cached_response(redis, key, cached_data)
        return cached_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/disease-profile/ontology/", tags=["Disease Profile"])
async def get_disease_ontology(
        disease_request: DiseaseRequest,  # Use the Pydantic model here
        redis: Redis = Depends(get_redis),  # Redis dependency for caching
        db: Session = Depends(get_db)  # Database session
) -> Dict[str, List[Dict]]:
    """
    Fetches the ontology (ancestors, anchor, and descendants) for a given disease.
    """
    disease: str = disease_request.disease.strip().lower().replace(" ", "_")
    # Generate a cache key for the request using target and disease list
    key: str = f"/disease-profile/ontology:{disease}"
    endpoint: str = "/disease-profile/ontology/"

    # Directory to store the cached JSON file
    cache_dir: str = "cached_data_json/disease"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the directory exists

    # File path for the JSON response
    file_path: str = os.path.join(cache_dir, f"{disease}.json")

    disease_record = db.query(Disease).filter_by(id=disease).first()
    # 1. Check if the cached JSON file exists
    if disease_record is not None:
        cached_file_path: str = disease_record.file_path
        print(f"Loading cached response from file: {cached_file_path}")
        cached_responses: Dict = load_response_from_file(cached_file_path)

        # Check if the endpoint response exists in the cached data
        if f"{endpoint}" in cached_responses:
            print(f"Returning cached response from file: {cached_file_path}")
            return cached_responses[f"{endpoint}"]

    # Check if cached response exists in Redis
    cached_response_redis: dict = await get_cached_response(redis, key)
    if cached_response_redis:
        print("Returning redis cached response")
        return cached_response_redis

    try:
        # File path for the JSONL file
        jsonl_file_path: str = "../disease_data/diseases_efo.jsonl"

        # Get EFO ID for the disease and adjust the format
        efo_id: str = find_disease_id_by_name(jsonl_file_path, disease_request.disease.strip().lower())
        print(f"EFO ID: {efo_id}")

        # Create adjacency lists
        adj_list: Dict[str, List[str]] = create_adjacency_list(jsonl_file_path)
        adj_list_reverse: Dict[str, List[str]] = create_reverse_adjacency_list(jsonl_file_path)

        # Find ancestors and descendants
        ancestors: Set[str] = find_ancestors(efo_id, adj_list)
        descendants: Set[str] = set(adj_list_reverse.get(efo_id, []))

        combined_set: Set[str] = ancestors | descendants  # Using the union operator
        combined_set.add(efo_id)

        # Log the ancestors and descendants for debugging purposes
        print("Ancestors: ", ancestors)
        print("Descendants: ", descendants)

        # Prepare the response data list
        response_data: List[Dict] = []

        # Extract data for descendants, anchor, and ancestors
        response_data.extend(extract_data_by_ids(jsonl_file_path, descendants, combined_set, "child"))
        response_data.extend(extract_data_by_ids(jsonl_file_path, {efo_id}, combined_set, "anchor"))
        response_data.extend(extract_data_by_ids(jsonl_file_path, ancestors, combined_set, "ancestor"))

        response: Dict[str, Any] = {"data": response_data}

        await set_cached_response(redis, key, response)

        if disease_record is not None:
            cached_responses = load_response_from_file(cached_file_path)
        else:
            cached_responses = {}

        cached_responses[f"{endpoint}"] = response

        if disease_record is None:
            save_response_to_file(file_path, cached_responses)
            new_record = Disease(id=disease, file_path=file_path)  # Create a new instance of the identified model
            db.add(new_record)  # Add the new record to the session
            db.commit()  # Commit the transaction to save the record to the database
            db.refresh(new_record)  # Refresh the instance to reflect any changes from the DB (like auto-generated
            # fields)
            print(f"Record with ID {disease} added to the disease table.")
        else:
            save_response_to_file(cached_file_path, cached_responses)

        # Return the data in the response
        return response

    except KeyError as e:
        # Handle cases where the EFO ID or its ancestors/descendants are not found
        raise HTTPException(status_code=404, detail=f"EFO ID not found for disease: {disease}.") from e
    except Exception as e:
        # Handle any other unforeseen errors
        raise HTTPException(status_code=500, detail=str(e)) from e


#################################### search apis ##############################################


@app.post("/search", tags=["Searching"])
async def search_disease(
        search_query: SearchQueryModel,  # Type from your Pydantic model
        redis: Redis = Depends(get_redis)  # Redis dependency for caching
) -> Dict[str, Any]:  # Return type hint for the response
    """
    Fetches the top drug,diseases for a given  query.
    """
    # Generate a cache key for the request using target and disease list
    key: str = f"/search-disease:{search_query.queryString.lower()}"

    # Check if cached response exists in Redis
    cached_response: Optional[Dict[str, Any]] = await get_cached_response(redis, key)
    if cached_response:
        print("Returning cached response")
        return cached_response

    variables: Dict[str, Any] = {
        "queryString": search_query.queryString,  # Assuming it's a string
        "entityNames": search_query.entityNames,  # Assuming it's a list of strings
        "page": search_query.page.dict()  # Convert the page object to a dictionary
    }

    # Send GraphQL request
    response: Dict[str, Any] = send_graphql_request(SearchQuery, variables)

    await set_cached_response(redis, key, response)

    return response


#################################### login apis ##############################################

@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect-- username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create token with role
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username,"role":"admin"}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/get-role")
def get_user_role(current_role: str = Depends(get_current_user_role)):
    return {"role": current_role}



#################################### apis to get html pages ##############################################

@app.get("/get-cover-page",tags=["HTML Pages"])
def fetch_landing_page() -> str:
    """
    API endpoint to fetch and return the cover page html.

    Returns:
        str: The landing page data as a string.
    """
    try:
        return get_conver_later_strapi()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#################################### Export feature apis ##############################################


@app.post("/export",tags=["Export API"])
async def get_excel_export(request: ExcelExportRequest):
    """
    Calls the `get_excel_export` API endpoint internally using TestClient.
    """
    try:
        # Prepare the request data for the DiseasesRequest model
        diseases=request.diseases
        filtered_diseases = [disease.strip().lower() for disease in diseases]
        target=request.target.strip().lower()
        endpoint: str=request.endpoint
        
        if endpoint=="/evidence/rna-sequence/":
            request_data = DiseasesRequest(diseases=filtered_diseases)
            # Make the POST request to the internal API endpoint
            response = client.post("/evidence/rna-sequence/", json=request_data.dict())
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.json())
            json_data=response.json()
            file_path = process_data_and_return_file_rna(json_data)
            return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="rna_seq_excel.xlsx")
        elif endpoint=="/market-intelligence/indication-pipeline/":
            print(endpoint)
            request_data = DiseasesRequest(diseases=filtered_diseases)
            # Make the POST request to the internal API endpoint
            response = client.post("/market-intelligence/indication-pipeline/", json=request_data.dict())
            print(response)
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.json())
            json_data=response.json()
            file_path = process_pipeline_data(json_data)
            return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="pipeline_indication_excel.xlsx")            
        elif endpoint=="/evidence/mouse-studies/":
            request_data = DiseasesRequest(diseases=filtered_diseases)
            # Make the POST request to the internal API endpoint
            response = client.post("/evidence/mouse-studies/", json=request_data.dict())
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.json())
            json_data=response.json()
            file_path = process_mouse_studies(json_data)
            return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="animal_model_excel.xlsx")
        elif endpoint=="/evidence/search-patent/":
            request_data = TargetRequest(target=target,diseases=filtered_diseases)
            # Make the POST request to the internal API endpoint
            response = client.post("/evidence/search-patent/", json=request_data.dict())
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.json())
            json_data=response.json()
            file_path = process_patent_data(json_data)
            return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="patent_excel.xlsx")  
        elif endpoint=="/evidence/target-mouse-studies/":
            request_data = TargetOnlyRequest(target=target)
            # Make the POST request to the internal API endpoint
            response = client.post("/evidence/target-mouse-studies/", json=request_data.dict())
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.json())
            json_data=response.json()
            file_path = process_model_studies(json_data)
            return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="model_studies_excel.xlsx") 
        elif endpoint=="/market-intelligence/target-pipeline/":
            request_data = TargetRequest(target=target,diseases=filtered_diseases)
            # Make the POST request to the internal API endpoint
            response = client.post("/market-intelligence/target-pipeline/", json=request_data.dict())
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.json())
            json_data=response.json()
            file_path = process_target_pipeline(json_data)
            return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="target_pipeline_excel.xlsx") 
        elif endpoint=="/target-indication-pairs":
            request_data = DiseasesRequest(diseases=filtered_diseases)
            # Make the POST request to the internal API endpoint
            response = client.post("/target-indication-pairs", json=request_data.dict())
            if response.status_code != 200:
                raise HTTPException(status_code=response.status_code, detail=response.json())
            json_data=response.json()
            file_path=process_cover_letter_list_excel(json_data)
            return FileResponse(file_path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename="cover_letter_excel.xlsx") 
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="No functionality of export available")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/target-indication-pairs",tags=["Target Indication Pairs"])
async def get_target_indication_pairs(request:DiseasesRequest):
    """
    return the target indication pairs record from strapi.
    """
    
    try:
        diseases=request.diseases
        diseases = [disease.strip().lower() for disease in diseases]
        response={}
        for disease in diseases:
            response[disease]=get_target_indication_pairs_strapi(disease)
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/phenotypes/lexical", tags=["Phenotypes entity search"])
async def get_phenotypes_lexical(query: str, offset: int = 0, limit: int = 20, conn = Depends(get_db_connection)):
    """
    Endpoint to query phenotypes lexically based on input string.
    """
    try:
        results = lexical_phenotype_search(query, conn)
        count = len(results)
        data = results.iloc[offset:offset + limit].to_dict(orient="records")
        return {"count": count, "data": data} 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/genes/lexical", tags=["Genes"])
async def get_genes_lexical(query: str, offset: int = 0, limit: int = 20, conn = Depends(get_gene_search_db_connection)):
    """
    Endpoint to query genes based on input string.
    """
    try:
        results = lexical_gene_search(query, conn)
        count = len(results)
        data = results.iloc[offset:offset + limit].to_dict(orient="records")
        return {"count": count, "data": data} 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
@app.get("/cache-data",tags=["Caching Data"])
def cache_data():
    print("API endpoint '/cache-data' is called.")
    try:
        cache_all_data(client)  # Call the cache_all_data function
        return {"message": "Cache data operation completed"}
    except Exception as e:
        print(f"Error in '/cache-data' endpoint: {e}")
        return {"message": "An error occurred during the cache operation."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, workers=1)
