from neo4j_connector import fetch_data_from_neo4j
import pandas as pd
import json


def get_all_node_types():
    """To get all the labels/node_types available in robokop"""
    try:
        # Fetch data from Neo4j
        lst_of_dict_for_labels = fetch_data_from_neo4j("call db.labels()")

        # Check if the result is empty
        if not lst_of_dict_for_labels:
            raise ValueError("No labels found in the database.")

        # Extract labels
        lst_of_labels = [x['label'] for x in lst_of_dict_for_labels]
        return lst_of_labels

    except ValueError as ve:
        print(f"ValueError: {ve}")

    except Exception as e:
        raise RuntimeError(f"An error occurred while fetching node types: {e}")


def get_all_nodes_of_certain_type(node_type):
    """To get all the nodes of certain node_type/label avalible in robokop"""
    try:
        # Fetch data from Neo4j
        lst_of_dict_for_nodes = fetch_data_from_neo4j(f"MATCH (b:`{node_type}`) RETURN b.name as name")

        # Check if the result is empty
        if not lst_of_dict_for_nodes:
            raise ValueError("No nodes found for the selected label.")

        # Extract labels
        lst_of_nodes = [x['name'] for x in lst_of_dict_for_nodes]
        return lst_of_nodes

    except ValueError as ve:
        print(f"ValueError: {ve}")

    except Exception as e:
        raise RuntimeError(f"An error occurred while fetching node types: {e}")


def search_node_by_node_type_and_node_name(node_type, node_name):
    try:
        # Fetch data from Neo4j
        lst_of_dict_of_nodes = fetch_data_from_neo4j(f"MATCH (a:`{node_type}`)  where a.name contains '{node_name}' RETURN a.name as node")

        #lst_of_dict_for_nodes  = []
        # Check if the result is empty
        if not lst_of_dict_of_nodes:
            raise ValueError("No nodes found for the selected label and node name.")

        # Extract labels
        lst_of_nodes = [x['node'] for x in lst_of_dict_of_nodes]
        return lst_of_nodes

    except ValueError as ve:
        print(f"ValueError: {ve}")

    except Exception as e:
        raise RuntimeError(f"An error occurred while fetching node types: {e}")


def find_node_id_by_node_name(node_type, node_name):
    """Finds node id by node label and node name
    Args: node_type (str): label/type of the node
          node_name (str): name of the node
    Returns: returns unique id of the node
    """
    try:
        # Fetch data from Neo4j
        lst_of_dict_of_node = fetch_data_from_neo4j(f"MATCH (a:`{node_type}`)  where a.name = '{node_name}' RETURN a.id as node_id")

        # Check if the result is empty
        if not lst_of_dict_of_node:
            raise ValueError("No nodes found for the selected label and node name.")

        # Extract labels
        node_id = [x['node_id'] for x in lst_of_dict_of_node]
        return node_id

    except ValueError as ve:
        print(f"ValueError: {ve}")

    except Exception as e:
        raise RuntimeError(f"An error occurred while fetching node types: {e}")


def get_metapath(source_node_id, target_node_id, max_hops=3):
    try:
        query = (
            f"match p = shortestpath((g) - [*..{max_hops}]-(d)) where "
            f"g.id = '{source_node_id}' and d.id = '{target_node_id}'"
            "return [n in nodes(p) | {name: n.name, labels: labels(n)}] AS nodes, "
            "[rel IN relationships(p) | type(rel)] AS edges"
        )

        # Fetch data from Neo4j
        metapaths = fetch_data_from_neo4j(query)

        # Check if the result is empty
        if not metapaths:
            raise ValueError(f"No metapaths found between nodes {source_node_id} and {target_node_id}.")

        formatted_metapaths = []
        nodes = metapaths[0]['nodes']
        edges = metapaths[0]['edges']

        formatted_path = []

        for i in range(len(edges)):
            formatted_path.append({
                "node": {"name": nodes[i]['name']}
            })
            formatted_path.append({
                "relationship": {"type": edges[i]}
            })

        formatted_path.append({
            "node": {"name": nodes[-1]['name']}
        })

        formatted_metapaths.append({"path": formatted_path})

        return formatted_metapaths

    except ValueError as ve:
        print(f"ValueError: {ve}")

    except Exception as e:
        print(f"An error occurred while fetching the metapaths: {e}")


def find_direct_connections(source_node_type, source_node_id, target_node_type=None):
    try:
        if target_node_type:
            # Cypher query when both source and target labels are known
            query = (
                f"MATCH (n:`{source_node_type}`)-[r]-(m:`{target_node_type}`) "
                f"WHERE n.id = '{source_node_id}' "
                f"RETURN m.name as node_name, m.id as node_id, type(r) AS relationship"
                )
        else:
            # Cypher query when only the source label is known
            query = (
                f"MATCH (n:`{source_node_type}`)-[r]-(m) "
                f"WHERE n.id = '{source_node_id}' "
                "RETURN m.name as node_name, m.id as node_id, type(r) AS relationship"
                )

        # Execute the query
        direct_connections = fetch_data_from_neo4j(query)

        # Check if results are found
        if not direct_connections:
            print("No direct connections found for the specified node.")

        return direct_connections

    except ValueError as ve:
        print(f"ValueError: {ve}")

    except Exception as e:
        print(f"An error occurred while fetching direct connections: {e}")



#print(get_all_node_types())
#print(get_all_nodes_of_certain_type('biolink:Drug'))
#print(search_node_by_node_type_and_node_name('biolink:Disease', 'atopic'))
#print(find_node_id_by_node_name('biolink:Disease', 'atopic asthma'))
#print( get_metapath("NCBIGene:7293", "MONDO:0011292"))
#print(find_direct_connections("biolink:Gene", "NCBIGene:7293", 'biolink:Disease'))

