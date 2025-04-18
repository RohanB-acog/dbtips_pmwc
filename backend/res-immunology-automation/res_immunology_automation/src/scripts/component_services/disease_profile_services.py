# Define the type for the adjacency list
from typing import *
from collections import defaultdict
import json
import requests
import os

AdjacencyList = Dict[str, List[str]]


def create_adjacency_list(jsonl_file: str) -> AdjacencyList:
    """
    Create an adjacency list from a JSONL file.

    Each node in the list is directed from the 'id' to its 'parentIds'.

    Parameters:
    - jsonl_file (str): Path to the JSONL file containing disease data.

    Returns:
    - AdjacencyList: A defaultdict representing the adjacency list where keys are 'id' and
      values are lists of 'parentIds'.
    """
    # Using defaultdict to simplify handling missing keys
    adjacency_list: AdjacencyList = defaultdict(list)

    # Open the JSONL file and process each line
    with open(jsonl_file, 'r') as file:
        for line in file:
            # Parse each line as JSON
            data = json.loads(line)
            node_id: str = data['id']
            parent_ids: List[str] = data.get('parentIds', [])

            # Extend the adjacency list for the node
            adjacency_list[node_id].extend(parent_ids)

    return adjacency_list


# Define the type for the reverse adjacency list
ReverseAdjacencyList = Dict[str, List[str]]


def create_reverse_adjacency_list(jsonl_file: str) -> ReverseAdjacencyList:
    """
    Create a reverse adjacency list from a JSONL file.

    Each parentId will point to its child id(s).

    Parameters:
    - jsonl_file (str): Path to the JSONL file containing disease data.

    Returns:
    - ReverseAdjacencyList: A dictionary where keys are 'parentIds' and values
      are lists of 'id' that consider them as parents.
    """
    reverse_adjacency_list: ReverseAdjacencyList = {}

    # Open the JSONL file and process each line
    with open(jsonl_file, 'r') as file:
        for line in file:
            # Parse each line as JSON
            data = json.loads(line)
            node_id: str = data['id']
            parent_ids: List[str] = data.get('parentIds', [])

            # For each parentId, add the current node_id as its child
            for parent_id in parent_ids:
                if parent_id not in reverse_adjacency_list:
                    reverse_adjacency_list[parent_id] = []
                reverse_adjacency_list[parent_id].append(node_id)

    return reverse_adjacency_list


def find_ancestors(node: str, adjacency_list: AdjacencyList) -> Set[str]:
    """
    Find all ancestors of a given node in an adjacency list.

    Parameters:
    - node (str): The node for which we want to find the ancestors.
    - adjacency_list (AdjacencyList): A dictionary representing the adjacency list where keys are 'id'
      and values are lists of 'parentIds'.

    Returns:
    - Set[str]: A set of ancestor node IDs.
    """
    ancestors: Set[str] = set()  # To store the ancestors without duplicates

    # Recursive DFS function to explore ancestors
    def dfs(current_node: str):
        if current_node not in adjacency_list:
            return  # No parents to explore

        for parent in adjacency_list[current_node]:
            if parent not in ancestors:
                ancestors.add(parent)  # Add the parent to ancestors
                dfs(parent)  # Recursively find ancestors of the parent

    # Start the DFS traversal from the given node
    dfs(node)

    return ancestors


def extract_data_by_ids(jsonl_file: str, ids_to_extract: Set[str],all_nodes:Set[str], node_type: str) -> List[Dict]:
    """
    Extract specific entries from a JSONL file based on a set of IDs, and add a 'nodeType' field to each entry.
    Additionally, filter out parentIds that are not present in the 'ids_to_extract' set.

    Parameters:
    - jsonl_file (str): Path to the JSONL file.
    - ids_to_extract (Set[str]): A set of IDs to filter and extract data for.
    - node_type (str): A string to be added to each extracted data with the key 'nodeType'.

    Returns:
    - List[Dict]: A list of dictionaries, each representing an extracted entry with an additional 'nodeType' field
      and filtered 'parentIds'.
    """
    extracted_data: List[Dict] = []

    # Open the JSONL file and process each line
    with open(jsonl_file, 'r') as file:
        for line in file:
            # Parse each line as JSON
            data = json.loads(line)
            node_id: str = data['id']

            # Check if the current node's ID is in the set of IDs to extract
            if node_id in ids_to_extract:
                # Filter the parentIds: keep only those that are present in ids_to_extract
                if 'parentIds' in data:
                    data['parentIds'] = [pid for pid in data['parentIds'] if pid in all_nodes]

                # Add the 'nodeType' field
                data['nodeType'] = node_type

                # Append the filtered data to the list
                extracted_data.append(data)

    return extracted_data


def get_disease_description_strapi(disease_name: str) -> Optional[str]:
    """
    Fetches the description of a disease from Strapi based on the provided disease name.

    Args:
        disease_name (str): The name of the disease to fetch the description for.

    Returns:
        Optional[str]: The description of the disease if found, None otherwise.
    """
    STRAPI_BASE_URL = os.getenv("STRAPI_BASE_URL")
    # Define the API endpoint, dynamically include the disease name
    url = f"{STRAPI_BASE_URL}/api/disease-overviews?filters[disease][$eqi]={disease_name}&fields[0]=description"

    # Retrieve the API token (replace with a secure retrieval method for production)
    api_token = os.getenv('STRAPI_API_TOKEN')

    if not api_token:
        print("API token not found in environment variables. Set 'STRAPI_API_TOKEN'.")
        return None

    # Define the headers with authorization token
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    try:
        # Send a GET request to retrieve data
        response = requests.get(url, headers=headers)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            
            # Extract the description field from the response
            if data["data"] and len(data["data"]) > 0:
                return data["data"][0].get("description", None)
            else:
                print("No data found for the specified disease.")
                return None
        else:
            # If there's an error, print the status code and error message
            print(f"Failed to fetch data. Status code: {response.status_code}")
            print(response.text)
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
