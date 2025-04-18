import pandas as pd
from collections import defaultdict
from metapaths import get_hop_chain_paths_with_recursion
from json_utils import process_json_to_dataframe
from json_utils import create_source_destination_relation_dict


json_file_path = "../../kg_data/meta_knowledge_graph.json"
df = process_json_to_dataframe(json_file_path)

# Create the dictionary from the updated data
source_destination_relation_dict = create_source_destination_relation_dict(df)


# Function to build unique intermediate nodes based on dynamic hop levels
def build_unique_nodes_by_n_hop(hop_dict):
    result_dict = {}

    # For 1_hop, no intermediate nodes, return an empty set
    result_dict['1_hop'] = dict()

    # For each hop level in the hop dictionary
    for hop_key, hops in hop_dict.items():
        hop_level = int(hop_key.split('_')[0])  # Extract hop level as an integer

        # Skip 1_hop since it has no intermediate nodes
        if hop_level == 1:
            continue

        # Dictionary to store unique intermediate nodes for this hop level
        intermediate_node_dict = defaultdict(set)

        for hop in hops:
            nodes = hop.split('-')  # Split hop into individual nodes

            # Collect intermediate nodes dynamically based on hop level
            for i in range(1, hop_level):  # Dynamically collect intermediate nodes
                intermediate_node_dict[f'intermediate_node_{i}'].add(
                    nodes[i])  # Add each intermediate node dynamically

            # if hop_level == 2:
            #     # For 2_hop: Source -> Intermediate -> Target
            #     intermediate_node_dict['intermediate_node_1'].add(nodes[1])  # Only 1 intermediate node
            # else:
            #     # For n_hop where n >= 3: Source -> Intermediate(s) -> Target
            #     for i in range(1, hop_level):  # Dynamically collect intermediate nodes
            #         intermediate_node_dict[f'intermediate_node_{i}'].add(
            #             nodes[i])  # Add each intermediate node dynamically

        # Convert sets to lists and add to result
        result_dict[hop_key] = {k: list(v) for k, v in intermediate_node_dict.items()}

    return result_dict


def generate_edges_for_n_hops(n_hop_node_dict, relation_dict):
    """Get edges for each node for each hop in the hop node dict"""
    n_hop_inter_nodes_and_edges_dict = dict()

    for key, value in n_hop_node_dict.items():
        hop_level = int(key.split('_')[0])

        # Generate dynamic columns for nodes
        node_cols = []
        if hop_level > 0:
            for i in range(1, hop_level):  # Create node columns dynamically
                node_cols.append(f'inter_nodes_{i}')

        for i in range(1, hop_level+1):  # Create edge columns dynamically
            node_cols.append(f'relation_{i}')

        lst_of_all_paths_with_their_relations = []
        for path in value:
            elements = path.split('-')
            intermediate_nodes = elements[1:-1]

            # Create a list of tuples, starting from the first element and progressively adding more
            for i in range(len(elements) - 1):
                node_tuple = (elements[i], elements[i + 1])
                edges_for_node_tuple = relation_dict[node_tuple]
                intermediate_nodes.append(str(edges_for_node_tuple))

            lst_of_all_paths_with_their_relations.append(intermediate_nodes)

        inter_nodes_edges_df = pd.DataFrame(lst_of_all_paths_with_their_relations, columns=node_cols)

        n_hop_inter_nodes_and_edges_dict[key] = inter_nodes_edges_df

    return n_hop_inter_nodes_and_edges_dict


source = 'biolink:Gene'
target = 'biolink:Disease'
n_levels = 4

hop_chain_paths_with_destination = get_hop_chain_paths_with_recursion(df, source, n_levels, target)
edges_result = generate_edges_for_n_hops(hop_chain_paths_with_destination, source_destination_relation_dict)

# print(hop_chain_paths_with_destination.keys())
# for k, v in hop_chain_paths_with_destination.items():
#     print(k, len(v))
#
# print("edges_result", edges_result.keys())
# for key, values in edges_result.items():
#
#     print(key, values.shape)
#     values.to_csv(f'./gene_disease_{key}.csv', index=False)


