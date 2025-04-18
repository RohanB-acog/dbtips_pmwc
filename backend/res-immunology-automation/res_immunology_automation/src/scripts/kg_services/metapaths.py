import pandas as pd
from collections import defaultdict
from json_utils import process_json_to_dataframe
from json_utils import create_source_destination_relation_dict


json_file_path = "../../kg_data/meta_knowledge_graph.json"
df = process_json_to_dataframe(json_file_path)

# Create the dictionary from the robokop json data
source_destination_relation_dict = create_source_destination_relation_dict(df)


# Recursive function to create hop chain paths
def explore_paths(graph, current_node, path, current_hop, max_hops, hop_chain_paths, destination):
    """Recursively explores paths in robokop upto a specified maximum number of hops.
    Args: graph (dict): dictionary for the source and target
          current_node (str): The current node in the path exploration
          path (list):
          current_hop (int): The current hop level
          max_hops (int): Maximum number of hops allowed for the path exploration
          hop_chain_path (dict): A dictionary where keys are strings indicating the hop level (e.g. '1_hop', '2_hop')
          and values are lists of paths found at that hop level.
          destination (str, optional): The destination node type to stop the recursion
    """
    # Stop recursion if we've reached the destination or the maximum hop level
    if current_hop > max_hops:
        return

    # If we've reached the destination, add the final path to the hop chain and stop
    if destination is not None and current_node == destination:
        hop_chain_paths[f'{current_hop}_hop'].append('-'.join(path))
        return  # Stop further exploration for this path

    if destination is None and current_hop > 0:
        hop_chain_paths[f'{current_hop}_hop'].append('-'.join(path))

    # Recur for each neighbor (relation and destination node)
    for neighbor in graph[current_node]:
        explore_paths(graph, neighbor, path + [neighbor], current_hop + 1, max_hops, hop_chain_paths,
                      destination)


# Function to initialize the adjacency list and start recursion
def get_hop_chain_paths_with_recursion(graph_df, root, n, destination=None):

    # Create an adjacency list with relations from the DataFrame
    adjacency_list = defaultdict(set)

    for idx, row in graph_df.iterrows():
        adjacency_list[row['source']].add(row['destination'])

    # Dictionary to store the paths for each hop level
    hop_chain_paths = defaultdict(list)

    # Start the recursive exploration from the root node
    explore_paths(adjacency_list, root, [root], 0, n, hop_chain_paths, destination)

    # Ensure that each hop level has an empty list if no paths were found
    for i in range(1, n + 1):
        hop_chain_paths[f'{i}_hop'] = hop_chain_paths.get(f'{i}_hop', [])

    return dict(hop_chain_paths)


root_node = "biolink:Gene"
n_levels = 2
destination_node = "biolink:Disease"

hop_chain_paths_with_destination = get_hop_chain_paths_with_recursion(df, root_node, n_levels)
print(hop_chain_paths_with_destination)
# print(hop_chain_paths_with_destination['1_hop'][:2])




