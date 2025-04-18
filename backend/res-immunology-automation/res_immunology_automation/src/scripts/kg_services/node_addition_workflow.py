from neo4j_connector import fetch_data_from_neo4j
from kg_utils import get_all_node_types
from json_utils import load_json
from qdrant_client import models, QdrantClient
from sentence_transformers import SentenceTransformer
import json


def get_node_types_online():  # Might need to fetch from config
    """should be done using query or the metagraph json
    To show all the available node types in the dropdown"""
    all_labels = get_all_node_types()
    return all_labels


def get_node_types_offline(json_file_path):   # Might need to fetch from config
    """To show all the available node types in the dropdown when mode is offline
    Args: json_file_path(str): Path of the backned graph json
    Returns : List of all the uniqie node types available in the backend graph json"""
    all_labels = set()
    json_data = load_json(json_file_path)
    for item in json_data['elements']:
        entry = item.get('data', {})
        node_type = entry.get('type')
        all_labels.add(node_type)
    return all_labels


def get_nodes_based_on_user_query(mode, node_type, user_query):
    """convention: embedding collection name would be same as "{node_type}_{mode}" for each node type
    To match the user given node in the online(robokop) graph using the vector embeddings
    Args: mode(str): 'online' or 'offline'
          node_type (str): To match the query for the selected node type
          user query(str): user query which will be matched with vector embeddings
    Returns: List of top 10 matches with the user query"""

    collection_name = node_type + "_" + mode
    encoder = SentenceTransformer("all-MiniLM-L6-v2")
    client = QdrantClient(url="http://localhost:6333")
    hits = client.query_points(
        collection_name=collection_name,
        query=encoder.encode(user_query).tolist(),
        limit=10,
    ).points

    return hits


def get_existing_nodes_in_graph(json_data):
    """To get all the existing nodes in the subgraph json"""
    existing_nodes_in_subgraph = set()
    for item in json_data['elements']:
        nodes = dict()
        entry = item.get('data', {})
        nodes['node_id'] =  entry.get('id')
        nodes['node_name'] = entry.get('label')
        nodes['node_type'] = entry.get('type')
        existing_nodes_in_subgraph.add(nodes)

    return existing_nodes_in_subgraph


def find_newly_added_node_connections_online(node_type, node_id, lst_of_target_nodes):
    """When node needs to be added in online mode (from robokop to the backend subgraph)
    Args: node_type (str): Label of the node to optimize the query
          node_id (str): node id of the selected node among top 10 results
          lst_of_target_nodes (list): list of existing nodes in the backend graph to get the connections
    Returns: list of dictionaries containing the new node data along with its connections with the existing nodes
           """
    try:
        query = (f"MATCH(source: `{node_type}`) - [r] - (target) "
                 f"WHERE elementID(source) ends with '{node_id}' and target.id IN{lst_of_target_nodes} "
                 f"RETURN elementID(source) as source_element_id, labels(source) as labels, source, type(r) as relation, "
                 f"properties(r) as edge_properties, elementID(target) as target_element_id "
                 )

        results = fetch_data_from_neo4j(query)

        # Append all the results in the json (depends on json structure)
        data_to_be_added = []
        first_result = results[0]
        source_node = dict()
        source_node['id'] = first_result['source_element_id'].split(":")[-1]
        source_node['label'] = first_result['source']['name']
        source_node['type'] = node_type
        source_node['labels'] = first_result['labels']
        source_node['properties'] = first_result['source']

        data_to_be_added.append({"data": source_node})

        for result in results:
            relations = dict()
            print("relations_initial", relations)
            relations['source'] = source_node['id']
            relations['target'] = result['target_element_id'].split(":")[-1]
            relations['label'] = result['relation']
            relations['properties'] = result['edge_properties']
            print("relations", relations)
            data_to_be_added.append({"data": relations})

        return data_to_be_added   # JSON will be updated

    except ValueError as ve:
        print(f"ValueError: {ve}")

    except Exception as e:
        raise RuntimeError(f"An error occurred while fetching node types: {e}")


def find_newly_added_node_connections_offline(node_id, lst_of_target_nodes, backend_json_data):
    """When node needs to be added form the backend subgraph to the graph which will be shown on the UI
    Args: node_id(str): node id of the selected node among top 10 results
          lst_of_target_nodes (list): list of existing nodes in the UI graph to get the connections with new node
          backend_json_data: To get the node data from the backend graph json to the dynamic json
    Returns: list of dictionaries containing the new node data along with its connections with the existing nodes"""
    node_connections = []
    for target_id in lst_of_target_nodes:
        for item in backend_json_data['elements']:
            data = item.get('data', {})

            # Check if the item itself matches the node_id
            if item.get('id') == str(node_id):
                node_connections.append(item)

            # Check for connections between the node_id and target_id
            if data.get('source') == node_id and data.get('target') == target_id:
                node_connections.append({"data": {
                    'source': data['source'],
                    'target': data['target'],
                    'relationship': data['label'],
                    'properties': data.get('properties', {})
                }})

    return node_connections  # JSON will be updated


def update_json(connection):
    for data in connection:
        json.dumps(data)


def add_new_node_relations(mode, node_type, node_id, backend_json_data, json_data):
    """Add node based on the mode selected by user"""
    if mode == 'online':
        # From robokop to backend graph
        lst_of_target_nodes_backend = get_existing_nodes_in_graph(backend_json_data)
        bac_node_connections = find_newly_added_node_connections_online(node_type, node_id, lst_of_target_nodes_backend)
        update_json(bac_node_connections)

        # From backend graph to UI graph
        lst_of_target_nodes = get_existing_nodes_in_graph(json_data)
        node_connections = find_newly_added_node_connections_offline(node_id, lst_of_target_nodes, backend_json_data)
        update_json(node_connections)

    else:
        # From backend graph to UI graph
        lst_of_target_nodes = get_existing_nodes_in_graph(json_data)
        node_connections = find_newly_added_node_connections_offline(node_id, lst_of_target_nodes, backend_json_data)
        update_json(node_connections)

