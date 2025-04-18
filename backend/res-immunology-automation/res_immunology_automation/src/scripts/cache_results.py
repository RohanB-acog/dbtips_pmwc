from api_models import (
    TargetRequest,
    DiseasesRequest,
    DiseaseRequest,
    TargetOnlyRequest
)
from typing import List, Dict, Set
import json
from fastapi.testclient import TestClient


def cache_all_data(client: TestClient):
    # Load target-disease mapping from a JSON file
    with open("../disease_data/diseases_to_cache.json") as f:
        unique_diseases: Set[str] = set(json.load(f))

    # Define endpoint categories
    diseases_only_endpoints = [
        "/evidence/literature/",
        "/evidence/mouse-studies/",
        "/evidence/network-biology/",
        "/evidence/top-10-literature/",
        "/disease-profile/details/",
        "/market-intelligence/indication-pipeline/",
        "/market-intelligence/kol/",
        "/market-intelligence/key-influencers/",
        "/evidence/rna-sequence/",
    ]

    disease_only_endpoints = [
        "/disease-profile/ontology/"
    ]


    # Call diseases-only endpoints
    for endpoint in diseases_only_endpoints:
        try:
            request_data = DiseasesRequest(diseases=list(unique_diseases))
            print(f"Calling {endpoint} with all diseases: {list(unique_diseases)}")
            response = client.post(endpoint, json=request_data.dict())
            print(f"Response for {endpoint}: {response.status_code} {response.json()}")
        except Exception as e:
            print(f"Error calling {endpoint} with all diseases: {e}")

    # Call disease-only endpoints
    for disease in unique_diseases:
        for endpoint in disease_only_endpoints:
            try:
                request_data = DiseaseRequest(disease=disease)
                print(f"Calling {endpoint} for disease: {disease}")
                response = client.post(endpoint, json=request_data.dict())
                print(f"Response for {endpoint}: {response.status_code} {response.json()}")
            except Exception as e:
                print(f"Error calling {endpoint} for disease {disease}: {e}")


  
