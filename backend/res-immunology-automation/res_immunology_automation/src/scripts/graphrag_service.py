# graphrag_service.py
import os
import urllib.parse
import numpy as np
import pandas as pd
import tiktoken
from os import getenv
from redis import Redis
import json
import re
from graphrag.query.indexer_adapters import read_indexer_entities, read_indexer_reports
from graphrag.query.llm.oai.chat_openai import ChatOpenAI
from graphrag.query.llm.oai.typing import OpenaiApiType
from graphrag.query.structured_search.global_search.community_context import (
    GlobalCommunityContext,
)
from graphrag.query.structured_search.global_search.search import GlobalSearch
# Your GraphRAG-related configurations and logic
def create_graphrag_search_engine():
    api_key = getenv("OPENAI_API_KEY", None)
    llm_model = getenv("LLM_MODEL", "gpt-4o")
    
    llm = ChatOpenAI(
        api_key=api_key,
        model=llm_model,
        api_type=OpenaiApiType.OpenAI,
        max_retries=20,
    )
    
    token_encoder = tiktoken.get_encoding("cl100k_base")
    
    # Assuming you have pre-loaded the reports and entity data
    INPUT_DIR = getenv("GRAPHRAG_DATA_DIR", None)
    COMMUNITY_REPORT_TABLE = "create_final_community_reports"
    ENTITY_TABLE = "create_final_nodes"
    ENTITY_EMBEDDING_TABLE = "create_final_entities"
    COMMUNITY_LEVEL = 2
    
    entity_df = pd.read_parquet(f"{INPUT_DIR}/{ENTITY_TABLE}.parquet")
    report_df = pd.read_parquet(f"{INPUT_DIR}/{COMMUNITY_REPORT_TABLE}.parquet")
    entity_embedding_df = pd.read_parquet(f"{INPUT_DIR}/{ENTITY_EMBEDDING_TABLE}.parquet")
    
    reports = read_indexer_reports(report_df, entity_df, COMMUNITY_LEVEL)
    entities = read_indexer_entities(entity_df, entity_embedding_df, COMMUNITY_LEVEL)
    
    context_builder = GlobalCommunityContext(
        community_reports=reports,
        entities=entities,
        token_encoder=token_encoder,
    )
    
    context_builder_params = {
        "use_community_summary": False,
        "shuffle_data": True,
        "include_community_rank": True,
        "min_community_rank": 0,
        "community_rank_name": "rank",
        "include_community_weight": True,
        "community_weight_name": "occurrence weight",
        "normalize_community_weight": True,
        "max_tokens": 12_000,
        "context_name": "Reports",
    }
    
    map_llm_params = {
        "max_tokens": 1000,
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
    }
    
    reduce_llm_params = {
        "max_tokens": 2000,
        "temperature": 0.0,
    }
    
    search_engine = GlobalSearch(
        llm=llm,
        context_builder=context_builder,
        token_encoder=token_encoder,
        max_data_tokens=12_000,
        map_llm_params=map_llm_params,
        reduce_llm_params=reduce_llm_params,
        allow_general_knowledge=False,
        json_mode=True,
        context_builder_params=context_builder_params,
        concurrent_coroutines=32,
        response_type="list of 3-7 points",
    )
    
    return search_engine

def get_redis():
  """Connects to redis instance"""
  cache_conn = Redis(host=getenv("REDIS_HOST", None), port=6379, password=getenv("REDIS_PASSWORD", None), decode_responses=True)
  return cache_conn

def get_graphrag_answer(question: str):
    redis_client = get_redis()
    cache_key = f"graphrag:{question.strip()}"
    cached_response = redis_client.json().get(cache_key)

    if cached_response:
        return cached_response["response"], cached_response["llm_calls"], cached_response["prompt_tokens"]

    search_engine = create_graphrag_search_engine()
    result = search_engine.search(question)

    response_data = {
        "response": result.response,
        "llm_calls": result.llm_calls,
        "prompt_tokens": result.prompt_tokens
    }

    redis_client.json().set(cache_key, "$", response_data)

    return result.response, result.llm_calls, result.prompt_tokens

title_to_pmc_id_mapping = {
    "OX40-OX40L Inhibition for the Treatment of Atopic Dermatitis—Focus on Rocatinlimab and Amlitelimab":"36559247",
    "Unraveling Atopic Dermatitis: Insights into Pathophysiology, Therapeutic Advances, and Future Perspectives":"38474389",
    "Association of TNFSF4 (OX40L) polymorphisms with susceptibility to systemic sclerosis":"19778912",
    "Targeting Costimulatory Pathways in Systemic Sclerosis":"30619351",
    "Atopic dermatitis: an expanding therapeutic pipeline for a complex disease":"34417579",
    "Hidradenitis Suppurativa and Comorbid Disorder Biomarkers, Druggable Genes, New Drugs and Drug Repurposing—A Molecular Meta-Analysis":"35056940",
    "Contribution of plasma cells and B cells to hidradenitis suppurativa pathogenesis":"32853177",
    "The OX40 Axis is Associated with Both Systemic and Local Involvement in Atopic Dermatitis":"32176307",
    "Understanding the immune landscape in atopic dermatitis: The era of biologics and emerging therapeutic approaches":"30825336",
    "TNF superfamily control of tissue remodeling and fibrosis":"37465675"
}

def grabTitle(text:str)->str:
    return text.split("\n")[0]

def getPMCId(title:str)->str:
    return title_to_pmc_id_mapping.get(title, None)


def extract_first_last_phrases(text: str, phrase_length: int = 3):
    words = text.strip().split()
    
    phrases = [' '.join(words[i:i+phrase_length]) for i in range(0, len(words)-phrase_length+1, phrase_length)]
    
    if not phrases:
        return "", ""
    
    first_phrase = phrases[0] if len(phrases) > 0 else ""
    last_phrase = phrases[-1] if len(phrases) > 1 else ""
    
    return first_phrase, last_phrase

def load_paper_from_txt(pmc_id: str, folder_path: str) -> str:
    """Load the full paper content from a text file based on the PMC ID."""
    file_path = os.path.join(folder_path, f"{pmc_id}.txt")
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()  # Return the full text of the paper
    else:
        raise FileNotFoundError(f"Paper with PMC ID {pmc_id} not found in the folder.")

def add_publication_link_below_title(text: str, pmcid: str) -> str:
    """Add a 'Link to publication' line below the title with an href to EuropePMC."""
    lines = text.split("\n")
    
    # Assume the first line is the title
    title_line = lines[0].strip()
    
    # Create the 'Link to publication' href
    publication_link = f"<a href='https://europepmc.org/article/med/{pmcid}' target='_blank'>Link to publication</a>"
    
    # Insert the publication link as a new line right after the title
    lines.insert(1, publication_link)
    
    # Join the lines back into a single string
    return "\n".join(lines)

def highlight_chunk(text: str, first_phrase: str, last_phrase: str) -> str:
    """Highlight the portion of the text between the first and last phrases in one <span>."""
    # Find the start and end indices of the first and last phrases
    start_index = text.find(first_phrase)
    end_index = text.find(last_phrase)
    
    if start_index == -1 or end_index == -1:
        return text  # If the phrases are not found, return the original text
    
    # Add the length of the last phrase to get the full end index
    end_index += len(last_phrase)
    
    # Wrap the entire section between first and last phrases in one <span> tag
    highlighted_text = (
        text[:start_index] + 
        f"<span class='highlight'>{text[start_index:end_index]}</span>" + 
        text[end_index:]
    )
    
    return highlighted_text

def fetch_text_chunks(reference_id: int, communities_path: str, text_units_path: str, folder_path: str):
    try:
        report_with_text_chunks_df = pd.read_parquet(communities_path)
        text_units = pd.read_parquet(text_units_path)
        text_units['unpacked_document_ids'] = text_units["document_ids"].apply(lambda x: x[0])
        
        result_df = text_units.groupby('unpacked_document_ids').first().reset_index() 
        result_df["title"] = result_df["chunk"].apply(grabTitle)
        result_df["pmc_id"] = result_df["title"].apply(getPMCId)
        doc_id_to_pmc_id_mapping = dict(zip(result_df["unpacked_document_ids"], result_df["pmc_id"]))

        def map_doc_id_to_pmc_id(doc_id: str):
            return doc_id_to_pmc_id_mapping.get(doc_id, None)
        
        text_units["pmc_id"] = text_units["unpacked_document_ids"].apply(map_doc_id_to_pmc_id)

        text_unit_ids_final = []

        text_unit_ids = report_with_text_chunks_df.loc[
            report_with_text_chunks_df["raw_community"] == str(reference_id)
        ]["text_unit_ids"].values[0]

        if isinstance(text_unit_ids, str):
            text_unit_ids_final = text_unit_ids.split(',')
        elif isinstance(text_unit_ids, (np.ndarray, list)):
            text_unit_ids_final = [id.strip() for sublist in text_unit_ids for id in sublist.split(',')]
        else:
            text_unit_ids_final = list(text_unit_ids)

        # Take only the first chunk
        if text_unit_ids_final:
            first_text_unit_id = text_unit_ids_final[0]
            try:
                chunk = text_units[text_units['id'] == str(first_text_unit_id)]['chunk'].values[0]
                pmc_id = text_units[text_units['id'] == str(first_text_unit_id)]['pmc_id'].values[0]  
            except IndexError:
                return f"Text unit ID {first_text_unit_id} not found"
            
            # Extract first and last phrases from the chunk
            first_phrase, last_phrase = extract_first_last_phrases(chunk, 3)

            # Load the full paper content from the folder
            full_paper_text = load_paper_from_txt(pmc_id, folder_path)
            full_paper_with_link = add_publication_link_below_title(full_paper_text, pmc_id) 
            # Highlight the chunk in the full paper
            highlighted_paper = highlight_chunk(full_paper_with_link, first_phrase, last_phrase)
            # highlighted_paper_with_link = add_link_to_title(highlighted_paper, pmc_id)

            # Return the modified paper with the highlighting syntax
            return {"reference_id": reference_id, "highlighted_paper": highlighted_paper}
    except Exception as e:
        print(f"An error occurred: {e}")
        return None