def merge_nodes(node_id_1, node_id_2, preferred_node_name, preferred_node_properties, json_data):
    """Merges two nodes based on user preferences for name and properties.
    Args:node_id_1 (str): ID of the first node to merge.
        node_id_2 (str): ID of the second node to merge.
        preferred_name_node (str): ID of the node whose name should be used in the merged node.
        preferred_properties_node (str): ID of the node whose properties should be used in the merged node.
        nodes (list): List of dictionaries representing all nodes in the graph.
    Returns (dict): The merged node
    """
    merged_node = dict()
    merged_node["id"] = node_id_1 + '_' + node_id_2

    # Find nodes by ID
    node_1_data = next(
        (item.get('data', {}) for item in json_data['elements'] if item.get('data', {}).get('id') == str(node_id_1)),
        None)
    node_2_data = next(
        (item.get('data', {}) for item in json_data['elements'] if item.get('data', {}).get('id') == str(node_id_2)),
        None)

    # Choose name based on user preference
    if preferred_node_name == node_id_1:
        merged_node["label"] = node_1_data.get('label')

    elif preferred_node_name == node_id_2:
        merged_node["label"] = node_2_data.get('label')

    # Choose properties based on user preference
    if preferred_node_properties == node_id_1:
        merged_node["properties"] = node_1_data.get('properties')

    elif preferred_node_properties == node_id_2:
        merged_node["properties"] = node_2_data.get('properties')

    # Update nodes: Remove old nodes and add the merged node

    return merged_node
