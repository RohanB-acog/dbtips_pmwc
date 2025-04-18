import json
import pandas as pd
from collections import defaultdict


# Function to load data from a JSON file for offline mode
def load_json(json_file_path):
    """Load data from a JSON file."""
    try:
        with open(json_file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print("JSON file not found.")
        return []


def process_json_to_dataframe(json_file_path):
    """ To create dataframe from meta_knowledge_graph.json to get the nodes and edges data for robokop
    (This json does not have the general nodes like 'namedthing')
    Args: json_file_path (str): JSON file path for meta_knowledge_graph.json which is downloaded from robokop
    Returns: Returns a dataframe having three columns. ['source', 'destination', 'relation']
    """

    with open(json_file_path, 'r') as file:
        data = json.load(file)

    lst_all = []
    for i in data['edges']:
        source = i['subject']
        relation = i['predicate']
        target = i['object']
        lst_all.append([source, relation, target])

    columns = ['source', 'relation', 'destination']
    df = pd.DataFrame(lst_all, columns=columns)
    return df


# Function to create dictionary with unique (source, destination) pairs as keys
def create_source_destination_relation_dict(json_df):
    """ To create a dictionary for unique pairs of (source, target) as key and 'relations' as value"""

    pair_dict = defaultdict(list)

    # Iterate over the DataFrame rows
    for idx, row in json_df.iterrows():

        # Create a key from the (source, destination) pair
        key = (row['source'], row['destination'])
        relation = row['relation']

        # Append the relation to the list if it doesn't already exist
        if relation not in pair_dict[key]:
            pair_dict[key].append(relation)

    return dict(pair_dict)



