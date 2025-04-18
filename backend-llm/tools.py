from langchain.tools import tool
import psycopg2
from collections import defaultdict
import os

DB_CONFIG = {
    "dbname": os.environ["AACT_DB_NAME"],
    "user": os.environ["AACT_DB_USER"],
    "password": os.environ["AACT_DB_PASSWORD"],
    "host": os.environ["AACT_DB_HOST"],
    "port": os.environ["AACT_DB_PORT"],
}

def get_db_connection():
    """
    Helper function to create a new database connection.
    """
    try:
        return psycopg2.connect(**DB_CONFIG)
    except psycopg2.Error as e:
        raise RuntimeError(f"Failed to connect to the database: {str(e)}")

@tool
def query_clinical_trial_data(nct_id: str, columns: list):
    """
    Retrieves clinical trial information for a given nct_id (`also referred to as trial id`).

    Parameters:
    - nct_id (str): The unique identifier of the clinical trial. This is a mandatory field. Example: "NCT04380038"
    - columns (list): The columns to retrieve for the trial. Valid options are:
          'nct_id', 'description', 'outcome_type', 'measure', 'time_frame',
          'intervention_type', 'intervention_name', 'intervention_description'

    Returns:
    - A dictionary containing the requested data in a structured format.
    """

    # Define valid columns
    valid_columns = [
        'nct_id', 'description', 'outcome_type', 'measure', 'time_frame',
        'intervention_type', 'intervention_name', 'intervention_description'
    ]

    # Validate `nct_id`
    if not nct_id:
        raise ValueError("Error: The `nct_id` parameter is mandatory and cannot be empty.")
    if not isinstance(nct_id, str):
        raise ValueError("Error: The `nct_id` parameter must be a string.")

    # Validate `columns`
    if not columns:
        raise ValueError("Error: At least one column must be specified.")
    invalid_columns = [col for col in columns if col not in valid_columns]
    if invalid_columns:
        raise ValueError(f"Error: The following columns are invalid: {invalid_columns}. Valid options are: {valid_columns}.")
   

    # Map columns to their respective tables
    column_table_mapping = {
        'nct_id': 'interventions.nct_id',
        'description': 'brief_summaries.description',
        'outcome_type': 'design_outcomes.outcome_type',
        'measure': 'design_outcomes.measure',
        'time_frame': 'design_outcomes.time_frame',
        'intervention_type': 'interventions.intervention_type',
        'intervention_name': 'interventions.name',
        'intervention_description': 'interventions.description'
    }

    try:
        # Build SELECT clause and gather necessary tables
        select_clauses = []
        required_tables = set()

        for col in columns:
            mapped_column = column_table_mapping[col]
            select_clauses.append(mapped_column)
            required_tables.add(mapped_column.split('.')[0])

        # Build FROM and JOIN clauses
        base_table = "interventions"
        join_clauses = []
        for table in required_tables:
            if table != base_table:
                join_clauses.append(f"LEFT JOIN {table} ON {base_table}.nct_id = {table}.nct_id")

        # Construct the SQL query
        query = f"""
            SET search_path TO ctgov, public;
            SELECT {', '.join(select_clauses)}
            FROM {base_table}
            {' '.join(join_clauses)}
            WHERE {base_table}.nct_id = %s
        """
        print(f"Executing Query:\n{query}")  # Debugging

        # Connect to the database and execute the query
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (nct_id,))
                rows = cursor.fetchall()

        # Process the results and group by `nct_id`
        result = defaultdict(lambda: {"design_outcomes": []})
        for row in rows:
            trial_data = dict(zip(columns, row))

            # Add non-outcome fields only once per trial
            if "nct_id" not in result[nct_id]:
                result[nct_id].update({
                    k: v for k, v in trial_data.items() if k not in ["outcome_type", "measure", "time_frame"]
                })

            # Append outcome-specific data
            if "outcome_type" in trial_data and trial_data["outcome_type"]:
                result[nct_id]["design_outcomes"].append({
                    "outcome_type": trial_data["outcome_type"],
                    "measure": trial_data["measure"],
                    "time_frame": trial_data["time_frame"]
                })

        # Convert to list
        final_result = list(result.values())
        return final_result if final_result else f"No data found for nct_id: {nct_id}"

    except Exception as e:
        raise ValueError(f"Error while querying the database: {str(e)}")


@tool
def query_inclusion_exclusion_criteria(nct_id: str, columns: list):
    """
    Retrieves inclusion/exclusion(eligibility) criteria for a trial with the given nct_id (`also referred to as trial id`).

    Parameters:
    - nct_id (str): The unique identifier of the clinical trial. This is a mandatory field. Example: "NCT04380038"
    - columns (list): The columns to retrieve for the trial. Valid options are:
        'gender', 'minimum_age', 'maximum_age', 'healthy_volunteers', 'adult', 'child', 'older_adult'

    Returns:
    - A dictionary containing the requested inclusion/exclusion criteria or an error message if validation fails.
    """

    # Define valid columns
    valid_columns = [
        'nct_id',
        'gender', 
        'minimum_age', 
        'maximum_age', 
        'healthy_volunteers', 
        'adult', 
        'child', 
        'older_adult'
    ]

    # Validate nct_id
    if not nct_id:
        raise ValueError("Error: The `nct_id` parameter is mandatory and cannot be empty.")
    if not isinstance(nct_id, str):
        raise ValueError("Error: The `nct_id` parameter must be a string.")

    # Validate columns
    if not columns:
        raise ValueError("Error: At least one column must be specified.")
    invalid_columns = [col for col in columns if col not in valid_columns]
    if invalid_columns:
        raise ValueError(f"Error: The following columns are invalid: {invalid_columns}. Valid options are: {valid_columns}.")

    # Build the query
    try:
        # Build SELECT clause
        select_clauses = [f"eligibilities.{col}" for col in columns]

        # Query for inclusion/exclusion criteria
        query = f"""
            SET search_path TO ctgov, public;
            SELECT eligibilities.nct_id, {', '.join(select_clauses)}
            FROM eligibilities
            WHERE eligibilities.nct_id = %s
        """
        print(f"Executing Query: {query}")  # Debugging

        # Connect to the database and execute the query
        with get_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(query, (nct_id,))
                results = cursor.fetchall()

        # Convert results to a list of dictionaries
        result_list = [
            {"nct_id": row[0], **dict(zip(columns, row[1:]))} for row in results
        ]

        return result_list if result_list else f"No inclusion/exclusion data found for nct_id: {nct_id}"

    except Exception as e:
        raise ValueError(f"Error while querying the database: {str(e)}")