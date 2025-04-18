import requests
import os
from typing import List, Dict, Any, Optional

# Define constants for the API URLs
BIOGRID_API_KEY: str = os.getenv('BIOGRID_API_KEY')
LIST_OF_SCREENS_FOR_TARGET_URL: str = ("https://orcsws.thebiogrid.org/genes/?format=json&name={"
                                       "target}&hit=yes&accessKey={api_key}")
LIST_ALL_SCREENS_URL: str = ("https://orcsws.thebiogrid.org/screens/?format=json&libraryType=crispra%7Ccrisprn"
                             "&accessKey={api_key}")


def fetch_list_of_screens_for_target(target: str) -> Optional[List[Dict[str, Any]]]:
    """
    Fetches the list of screens for a given target from the BioGRID API.

    Parameters:
    - target (str): The target name to search for.

    Returns:
    - Optional[List[Dict[str, Any]]]: List of screens for the target, or None if the API fails.
    """
    # Prepare the URL by formatting with the target and API key
    url: str = LIST_OF_SCREENS_FOR_TARGET_URL.format(target=target, api_key=BIOGRID_API_KEY)

    # Send a GET request to the API
    response: requests.Response = requests.get(url)

    # If the request is successful, return the JSON data
    if response.status_code == 200:
        return response.json()  # Assuming the API returns a list of screens in JSON format
    else:
        print(f"Failed to fetch screens for target {target}: {response.status_code}")
        return None


def fetch_all_screens() -> Optional[List[Dict[str, Any]]]:
    """
    Fetches all screens from the BioGRID API.

    Returns:
    - Optional[List[Dict[str, Any]]]: List of all screens, or None if the API fails.
    """
    # Prepare the URL by formatting with the API key
    url: str = LIST_ALL_SCREENS_URL.format(api_key=BIOGRID_API_KEY)

    # Send a GET request to the API
    response: requests.Response = requests.get(url)

    # If the request is successful, return the JSON data
    if response.status_code == 200:
        return response.json()  # Assuming the API returns a list of all screens in JSON format
    else:
        print(f"Failed to fetch all screens: {response.status_code}")
        return None


def find_matching_screens_for_target(target: str) -> List[Dict[str, Any]]:
    """
    Finds matching screens for the given target by cross-referencing data from both APIs.

    Parameters:
    - target (str): The target name to search for.

    Returns:
    - List[Dict[str, Any]]: List of matched screens for the target in the order of target_screen_ids.
    """
    if target is None:
        return []

    # Fetch the list of screens for the target
    list_of_screens_for_target: Optional[List[Dict[str, Any]]] = fetch_list_of_screens_for_target(target)

    if type(list_of_screens_for_target) == dict and 'STATUS' in list_of_screens_for_target and \
            list_of_screens_for_target['STATUS'] == 'ERROR':
        # print(list_of_screens_for_target)
        list_of_screens_for_target = None

    # Fetch all screens
    list_all_screens: Optional[List[Dict[str, Any]]] = fetch_all_screens()

    # If either API response is None, return an empty list
    if list_of_screens_for_target is None or list_all_screens is None:
        return []

    # Extract Screen IDs from list_of_screens_for_target
    target_screen_ids: List[str] = [screen['SCREEN_ID'] for screen in list_of_screens_for_target]

    # Create a dictionary for quick lookup of all screens by SCREEN_ID
    all_screens_dict: Dict[str, Dict[str, Any]] = {screen['SCREEN_ID']: screen for screen in list_all_screens}

    # Filter the final result to return only the specified fields in the order of target_screen_ids
    filtered_results: List[Dict[str, Any]] = []

    for screen_id in target_screen_ids:
        screen = all_screens_dict.get(screen_id)  # Lookup the screen by SCREEN_ID
        # print(screen)
        if screen:  # Only process if the screen exists
            filtered_results.append(screen)

    return filtered_results

# find_matching_screens_for_target("TNFRSF4")

def fetch_subcellular_locations(uniprot_id: str) -> List[Dict[str, Any]]:
    """
    Fetch the subcellularLocations data from the comments section of a UniProt entry.

    :param uniprot_id: The UniProt ID of the protein (e.g., "O60674").
    :return: A list of dictionaries containing subcellularLocations data.
    :raises ValueError: If the subcellularLocations data is not found.
    """
    if not uniprot_id:
        return []

    url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}"
    try:
        response = requests.get(url)

        if response.status_code != 200:
            raise Exception(f"Failed to fetch data for {uniprot_id}. HTTP Status: {response.status_code}")

        data = response.json()

        # Extract comments section
        comments = data.get("comments", [])

        # Filter for commentType == "SUBCELLULAR LOCATION"
        for comment in comments:
            if comment.get("commentType") == "SUBCELLULAR LOCATION":
                return comment.get("subcellularLocations", [])
    except Exception as e:
        print(f"Error occurred: {e}")

    return []