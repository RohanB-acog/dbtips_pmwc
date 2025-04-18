
from typing import Dict, List
from duckdb import DuckDBPyConnection
from pandas import DataFrame
import os
import duckdb
from fastapi import HTTPException

db_file_path = "/app/database/entity_search.db"
gene_db_file_path= "/app/database/geneSearch/duckdb.db"
# To query the phenotype id and name
primary_phenotype_query = """
SELECT
   id,
   name,
   CASE
       WHEN id ILIKE (? || '%') THEN 'id: ' || id
       WHEN dbXRefs_text ILIKE ('%' || ? || '%') THEN 'dbXRef: ' || dbXRefs_text
       WHEN name ILIKE ? THEN 'name: ' || name
       WHEN name ILIKE (? || '%') THEN 'name: ' || name
       WHEN name ILIKE ('%' || ' ' || ? || '%') THEN 'name: ' || name
       ELSE NULL
   END AS matched_column
FROM
   phenotypes
WHERE
   id ILIKE (? || '%') OR
   dbXRefs_text ILIKE ('%' || ? || '%') OR
   name ILIKE ? OR
   name ILIKE (? || '%') OR
   name ILIKE ('%' || ' ' || ? || '%')
ORDER BY
   CASE
       WHEN name ILIKE ? THEN 1
       WHEN name ILIKE (? || '%') THEN 2
       WHEN name ILIKE ('%' || ' ' || ? || '%') THEN 3
       WHEN id ILIKE (? || '%') THEN 4
       WHEN dbXRefs_text ILIKE ('%' || ? || '%') THEN 5
       ELSE 6
   END
"""

# To query synonyms
secondary_phenotype_query = """
SELECT
   id,
   name,
   CASE
       WHEN synonyms_text ILIKE (? || '%') OR synonyms_text ILIKE ('%' || ' ' || ? || '%') THEN 'synonyms: ' || synonyms_text
       ELSE NULL
   END AS matched_column
FROM
   phenotypes
WHERE
   synonyms_text ILIKE (? || '%') OR synonyms_text ILIKE ('%' || ' ' || ? || '%')
"""

# Full text search query
fts_phenotype_query = """
WITH fts_results AS (
    SELECT 
        id, 
        name,
        synonyms_text,
        fts_main_phenotypes.match_bm25(id, ?, conjunctive := 1, fields := 'name') AS name_score,
        fts_main_phenotypes.match_bm25(id, ?, conjunctive := 1, fields := 'synonyms_text') AS synonym_score
    FROM phenotypes
)
SELECT id, name, matched_column
FROM (
    SELECT 
        id,
        name,
        'name: ' || name AS matched_column,
        name_score AS score
    FROM fts_results
    WHERE name_score IS NOT NULL
    UNION
    SELECT 
        id,
        name,
        'synonyms: ' || synonyms_text AS matched_column,
        synonym_score AS score
    FROM fts_results
    WHERE synonym_score IS NOT NULL
) AS all_matches
ORDER BY 
    CASE 
        WHEN matched_column ILIKE 'name:%' THEN 1
        WHEN matched_column ILIKE 'synonyms:%' THEN 2
    END,
    score DESC
"""

# catchall query
substring_query = """
SELECT
   id,
   name,
   CASE
       WHEN name ILIKE ('%' || ? || '%') THEN 'name: ' || name
       WHEN synonyms_text ILIKE ('%' || ? || '%') THEN 'synonyms: ' || synonyms_text
       ELSE NULL
   END AS matched_column
FROM
   phenotypes
WHERE
   name ILIKE ('%' || ? || '%') OR
   synonyms_text ILIKE ('%' || ? || '%')
ORDER BY
   CASE
       WHEN name ILIKE ('%' || ? || '%') THEN 1
       WHEN synonyms_text ILIKE ('%' || ? || '%') THEN 2
       ELSE 3
   END
"""
primary_prefix_query = """
SELECT
   id,
   approvedSymbol,
   CASE
       WHEN id ILIKE (? || '%') THEN 'id:' || id
       WHEN approvedSymbol ILIKE ? THEN 'approvedSymbol:' || approvedSymbol
       WHEN approvedSymbol ILIKE (? || '%') THEN 'approvedSymbol:' || approvedSymbol
       WHEN approvedSymbol ILIKE ('%' || ? || '%') THEN 'approvedSymbol:' || approvedSymbol
       WHEN EXISTS (
       SELECT 1 FROM UNNEST(dbXrefs) AS unnest WHERE unnest.id ILIKE (? || '%')
           ) THEN 'dbXref:' || (SELECT unnest.id FROM UNNEST(dbXrefs) AS unnest WHERE unnest.id ILIKE (? || '%') LIMIT 1)
       ELSE NULL
   END AS matched_column
FROM
   genes
WHERE
   id ILIKE (? || '%') OR
   approvedSymbol ILIKE ? OR
   approvedSymbol ILIKE (? || '%') OR
   approvedSymbol ILIKE ('%' || ? || '%') OR
   EXISTS (
       SELECT 1
       FROM UNNEST(dbXrefs) AS unnest
       WHERE unnest.id ILIKE (? || '%')
   )
ORDER BY
   CASE
       WHEN approvedSymbol ILIKE ? THEN 1
       WHEN id ILIKE (? || '%') THEN 2
       WHEN approvedSymbol ILIKE (? || '%') THEN 3
       WHEN approvedSymbol ILIKE ('%' || ? || '%') THEN 4
       WHEN EXISTS (
       SELECT 1
       FROM UNNEST(dbXrefs) AS unnest
       WHERE unnest.id ILIKE (? || '%')
   ) THEN 5
       ELSE 6
   END
"""


# To query additional fields like symbol synonyms and alternate ids
secondary_prefix_query = """
SELECT
   id,
   approvedSymbol,
   CASE
       WHEN array_length(array_filter(alternativeGenes, x -> x ILIKE (? || '%'))) > 0
           THEN 'alternativeGenes: ' || (array_filter(alternativeGenes, x -> x ILIKE (? || '%')))[1]
       WHEN EXISTS (
           SELECT 1 FROM UNNEST(symbolSynonyms) AS unnest WHERE unnest.label ILIKE (? || '%')
           ) THEN 'symbolSynonyms: ' ||
           (SELECT unnest.label FROM UNNEST(symbolSynonyms) AS unnest WHERE unnest.label ILIKE (? || '%') LIMIT 1)
       WHEN EXISTS (
           SELECT 1 FROM UNNEST(obsoleteSymbols) AS unnest WHERE unnest.label ILIKE (? || '%')
           ) THEN 'obsoleteSymbols: ' ||
           (SELECT unnest.label FROM UNNEST(obsoleteSymbols) AS unnest WHERE unnest.label ILIKE (? || '%') LIMIT 1)
       ELSE NULL
   END AS matched_column
FROM
   genes
WHERE
   array_length(array_filter(alternativeGenes, x -> x ILIKE (? || '%'))) > 0 OR
   EXISTS (
       SELECT 1
       FROM UNNEST(symbolSynonyms) AS unnest
       WHERE (unnest.label) ILIKE (? || '%')
   ) OR
   EXISTS (
       SELECT 1
       FROM UNNEST(obsoleteSymbols) AS unnest
       WHERE unnest.label ILIKE (? || '%')
   )
"""


# To query the gene name
name_prefix_query = """
SELECT
   id,
   approvedSymbol,
   CASE
       WHEN approvedName ILIKE ? OR approvedName ILIKE (? || '%') OR approvedName ILIKE ('%' || ' ' || ? || '%') THEN 'approvedName:' || approvedName
       ELSE NULL
   END AS matched_column
FROM
   genes
WHERE
   approvedName ILIKE ? OR approvedName ILIKE (? || '%') OR approvedName ILIKE ('%' || ' ' || ? || '%')
ORDER BY
   CASE
       WHEN approvedName ILIKE ? THEN 1
       WHEN approvedName ILIKE (? || '%') THEN 2
       WHEN approvedName ILIKE ('%' || ' ' || ? || '%') THEN 3
       ELSE 4
   END
"""


# To query the synonyms for gene name
synonym_prefix_query = """
SELECT
   id,
   approvedSymbol,
   CASE
       WHEN EXISTS (
           SELECT 1 FROM UNNEST(nameSynonyms) AS unnest
           WHERE unnest.label ILIKE ? OR unnest.label ILIKE (? || '%') OR unnest.label ILIKE ('%' || ' ' || ? || '%')
           ) THEN 'nameSynonyms: ' ||
           (SELECT unnest.label FROM UNNEST(nameSynonyms) AS unnest
            WHERE unnest.label ILIKE ? OR unnest.label ILIKE (? || '%') OR unnest.label ILIKE ('%' || ' ' || ? || '%') LIMIT 1)
       WHEN EXISTS (
           SELECT 1 FROM UNNEST(obsoleteNames) AS unnest 
           WHERE unnest.label ILIKE ? OR unnest.label ILIKE (? || '%') OR unnest.label ILIKE ('%' || ' ' || ? || '%')
           ) THEN 'obsoleteNames: ' ||
               (SELECT unnest.label FROM UNNEST(obsoleteNames) AS unnest 
               WHERE unnest.label ILIKE ? OR unnest.label ILIKE (? || '%') OR unnest.label ILIKE ('%' || ' ' || ? || '%') LIMIT 1)
       ELSE NULL
   END AS matched_column
FROM
   genes
WHERE
   EXISTS (
       SELECT 1
       FROM UNNEST(nameSynonyms) AS unnest
       WHERE unnest.label ILIKE ? OR unnest.label ILIKE (? || '%') OR unnest.label ILIKE ('%' || ' ' || ? || '%')
   ) OR
   EXISTS (
       SELECT 1
       FROM UNNEST(obsoleteNames) AS unnest
       WHERE unnest.label ILIKE ? OR unnest.label ILIKE (? || '%') OR unnest.label ILIKE ('%' || ' ' || ? || '%')
   )
"""


# Full text search query
fts_gene_query = """
WITH fts_results AS (
    SELECT 
        id, 
        approvedSymbol,
        approvedName,
        nameSynonyms,
        obsoleteNames,
        fts_main_genes.match_bm25(id, ?, conjunctive := 1, fields := 'approvedName') AS approvedName_score,
        fts_main_genes.match_bm25(id, ?, conjunctive := 1, fields := 'nameSynonyms') AS nameSynonyms_score,
        fts_main_genes.match_bm25(id, ?, conjunctive := 1, fields := 'obsoleteNames') AS obsoleteNames_score
    FROM genes
)
SELECT id, approvedSymbol, matched_column
FROM (
    SELECT 
        id,
        approvedSymbol,
        'approvedName: ' || approvedName AS matched_column,
        approvedName_score AS score
    FROM fts_results
    WHERE approvedName_score IS NOT NULL
    UNION ALL
    SELECT 
        id,
        approvedSymbol,
        'nameSynonyms: ' || array_to_string([syn.label for syn in nameSynonyms],', ') AS matched_column,
        nameSynonyms_score AS score
    FROM fts_results
    WHERE nameSynonyms_score IS NOT NULL
    UNION ALL
    SELECT 
        id,
        approvedSymbol,
        'obsoleteNames: ' || array_to_string([syn.label for syn in obsoleteNames],', ') AS matched_column,
        obsoleteNames_score AS score
    FROM fts_results
    WHERE obsoleteNames_score IS NOT NULL
) AS all_matches
ORDER BY 
    CASE 
        WHEN matched_column ILIKE 'approvedName%' THEN 1
        WHEN matched_column ILIKE 'nameSynonyms%' THEN 2
        WHEN matched_column ILIKE 'obsoleteNames%' THEN 3
    END, score DESC
"""

# Catchall query
substring_query = """
SELECT
   id,
   approvedSymbol,
   CASE
       WHEN approvedName ILIKE ('%' || ? || '%') THEN 'approvedName:' || approvedName
       WHEN EXISTS (
           SELECT 1 FROM UNNEST(nameSynonyms) AS unnest
           WHERE unnest.label ILIKE ('%' || ? || '%')
           ) THEN 'nameSynonyms: ' ||
           (SELECT unnest.label FROM UNNEST(nameSynonyms) AS unnest
            WHERE unnest.label ILIKE ('%' || ? || '%') LIMIT 1)
       WHEN EXISTS (
           SELECT 1 FROM UNNEST(obsoleteNames) AS unnest 
           WHERE unnest.label ILIKE ('%' || ? || '%')
           ) THEN 'obsoleteNames: ' ||
           (SELECT unnest.label FROM UNNEST(obsoleteNames) AS unnest 
            WHERE unnest.label ILIKE ('%' || ? || '%') LIMIT 1)
       ELSE NULL
   END AS matched_column
FROM
   genes
WHERE
   approvedName ILIKE ('%' || ? || '%') OR
   EXISTS (
       SELECT 1
       FROM UNNEST(nameSynonyms) AS unnest
       WHERE unnest.label ILIKE ('%' || ? || '%')
   ) OR
   EXISTS (
       SELECT 1
       FROM UNNEST(obsoleteNames) AS unnest
       WHERE unnest.label ILIKE ('%' || ? || '%')
   )
ORDER BY
   CASE
       WHEN approvedName ILIKE ('%' || ? || '%') THEN 1
       WHEN EXISTS (
           SELECT 1 FROM UNNEST(nameSynonyms) AS unnest
           WHERE unnest.label ILIKE ('%' || ? || '%') 
           ) THEN 2
       WHEN EXISTS (
           SELECT 1 FROM UNNEST(obsoleteNames) AS unnest 
           WHERE unnest.label ILIKE ('%' || ? || '%')
           ) THEN 3
       ELSE 4
   END 
"""
def get_db_connection() -> DuckDBPyConnection: 
    if not db_file_path:
        raise HTTPException(status_code=500, detail="Database path is not set")
    conn = duckdb.connect(db_file_path, read_only=True)
    try:
        yield conn
    finally:
        conn.close()

def get_gene_search_db_connection() -> DuckDBPyConnection: 
    if not gene_db_file_path:
        raise HTTPException(status_code=500, detail="Database path is not set")
    conn = duckdb.connect(gene_db_file_path, read_only=True)
    try:
        yield conn
    finally:
        conn.close()


def lexical_phenotype_search(search_string: str, conn: DuckDBPyConnection) -> DataFrame:
   """
   Query the database for phenotypes lexically matching the search term with a result limit.
  
   Parameters:
       search_term (str): The search term for filtering phenotypes.
       limit (int): Maximum number of results to return.
       conn (DuckDBPyConnection): The database connection.


   Returns:
       List[Dict]: Query results as a list of dictionaries.
   """
   query = f"({primary_phenotype_query}) UNION ALL ({fts_phenotype_query}) UNION ALL ({secondary_phenotype_query}) UNION ALL ({substring_query})"
   results = conn.execute(query, (search_string, ) * query.count('?')).df()
   results.drop_duplicates(subset = ['id', 'name'], keep = 'first', inplace = True)
   if results.empty:
    return DataFrame()
   return results

def lexical_gene_search(search_term: str, conn: DuckDBPyConnection) -> DataFrame:
   """
   Query the database for genes lexically matching the search term with a result limit.
  
   Parameters:
       search_term (str): The search term for filtering genes.
       conn (DuckDBPyConnection): The database connection.


   Returns:
       List[Dict]: Query results as a list of dictionaries.
   """
   query = f"({primary_prefix_query}) UNION ALL ({secondary_prefix_query}) UNION ALL ({name_prefix_query})  UNION ALL ({fts_gene_query}) UNION ALL ({synonym_prefix_query}) UNION ALL ({substring_query})"
   results = conn.execute(query, (search_term, ) * query.count('?')).df()
   results.drop_duplicates(subset = ['id', 'approvedSymbol'], keep = 'first', inplace = True)
   if results.empty:
    return DataFrame()
   return results
