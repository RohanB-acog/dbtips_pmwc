from neo4j_connector import fetch_data_from_neo4j
from json_utils import load_json

import pandas as pd
import json


def find_direct_connections_online(source_node_type, source_node_id, target_node_type=None):
    """Finds and returns the dirct connection of a specified in an online graph (Robokop)
    Args: source_node_type (str): Type of the source node (label in the graph database)
          source_node_id (str):  Unique id of the source node
          target_node_type (str, optional): Type of the target node to filter the connection

    Returns: List of dictionaries for the connected node. Each dictionary contains
            node_id: Id of the neighbour node
            node_name: name of the node
            node_type: Type/label of the node
            relation: Label of the relationship between the source node and the neighbour node
          """

    try:
        if target_node_type:
            # Cypher query when both source and target labels are known
            query = (
                f"MATCH (n:`{source_node_type}`)-[r]-(m:`{target_node_type}`) "
                f"WHERE elementId(n) = '{source_node_id}' "
                f"RETURN m.name as node_name, labels(m), elementId(m) as node_id, type(r) AS relationship"
            )
        else:
            # Cypher query when only the source label is known
            query = (
                f"MATCH (n:`{source_node_type}`)-[r]-(m) "
                f"WHERE id(n) = '{source_node_id}' "
                "RETURN m.name as node_name, labels(m), m.id as node_id, type(r) AS relationship"
            )

        # Execute the query
        direct_connections = fetch_data_from_neo4j(query)
        for i in direct_connections:
            i['node_label'] = i['labels(m)'][-1]
            i.pop('labels(m)', None)

        # Check if results are found
        if not direct_connections:
            print("No direct connections found for the specified node.")

        return direct_connections

    except ValueError as ve:
        print(f"ValueError: {ve}")

    except Exception as e:
        print(f"An error occurred while fetching direct connections: {e}")


# Function to get the node name and type by id for offline mode
def get_node_type_by_id(node_id, json_data):
    """Find and return the name and type of a node given its ID from JSON data."""

    for item in json_data['elements']:
        entry = item.get('data', {})
        if entry.get('id') == str(node_id):
            return entry.get('type'), entry.get('label')
    return None


# Function for finding neighbors with edges in offline mode
def find_direct_connections_offline(source_node_id, json_data, target_node_type=None):
    """Find direct neighbors of a node along with their edge connections using JSON data.
    Args: source_node_id(str): Unique id of the source node
          json data (dict): existing graph data (nodes and relations)
          target_node_type (str, optional): Type of the target node to filter the connection

    Returns: List of dictionaries for the connected node. Each dictionary contains
            node_id: Id of the neighbour node
            node_name: name of the node
            node_type: Type/label of the node
            relation: Label of the relationship between the source node and the neighbour node
          """
    neighbors_with_edges = []

    for item in json_data['elements']:
        entry = item.get('data', {})
        source = entry.get('source')
        target = entry.get('target')
        edge_label = entry.get('label')

        if source == str(source_node_id):
            node_type, node_name = get_node_type_by_id(target, json_data)
            if not target_node_type or (target_node_type == node_type):
                neighbors_with_edges.append({'node_id': target, 'node_name': node_name, 'relationship': edge_label, 'node_label':node_type})

        elif target == str(source_node_id):
            node_type, node_name = get_node_type_by_id(source, json_data)
            if not target_node_type or (target_node_type == node_type):
                neighbors_with_edges.append({'node_id': source, 'node_name': node_name, 'relationship': edge_label, 'node_label':node_type})

    print("neighbors_with_edges", len(neighbors_with_edges))
    if neighbors_with_edges:
        return neighbors_with_edges
    else:
        print(f"No neighbors found for node ID {source_node_id}.")
        return []


# Function to get the direct connections
def find_direct_connections(mode, source_node_type, source_node_id, json_data=None, target_node_type=None):
    """ Finds nad returns the direct connection of a specified node, either from the online graph(robokop)
    or using offline JSON data
    Args: mode (str): The mode of operation, 'online' or 'offline'
          source_node_type (str): Type/label of the source node
          source_node_id (str):  Unique id of source node
          json_data (dict): Provide data for offline mode
          target_node_type (str,optional):  type/label of the target node to filter the connections

   Returns: List of dictionaries for the connected node. Each dictionary contains
            node_id: Id of the neighbour node
            node_name: name of the node
            node_type: Type/label of the node
            relation: Label of the relationship between the source node and the neighbour node
    """
    if mode == "online":
        neighbours = find_direct_connections_online(source_node_type, source_node_id, target_node_type)
    else:
        neighbours = find_direct_connections_offline(source_node_id, json_data, target_node_type)
    return neighbours


# list of target node types
# capture direction
mode = 'online'

# online
source_node_type = "biolink:Disease"
# source_node_id = "MONDO:0006559"
target_node = "biolink:Gene"

# # offline
json_file_path = "/Users/reetikaM1/PycharmProjects/target-dossier/frontend/src/assets/dgpg.graph.json"
data = load_json(json_file_path)
source_node_id = "5445223"
# target_node = "Gene"

neighbours = find_direct_connections(mode, source_node_type, source_node_id, json_data=data, target_node_type=target_node)
for neigh in neighbours:
    print(neigh)

