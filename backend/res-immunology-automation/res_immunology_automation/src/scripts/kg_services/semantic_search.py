import pandas as pd
from qdrant_client import models, QdrantClient
from sentence_transformers import SentenceTransformer


# # lst_of_dict_for_labels = fetch_data_from_neo4j(
# #     "MATCH (g:`biolink:Disease`) RETURN g.id as node_id, g.name as node_name, g.description as node_description")
# # df = pd.DataFrame(lst_of_dict_for_labels)
# # csv_path = "../../kg_data/disease_nodes_all.csv"  # Specify the path to save the CSV
# # df.to_csv(csv_path, index=False)

nodes = pd.read_csv("../../kg_data/disease_nodes_all.csv")
data_list = nodes.to_dict(orient="records")


# # Initialize the encoder and client
encoder = SentenceTransformer("all-MiniLM-L6-v2")
client = QdrantClient(url="http://localhost:6333")
collection_name = "disease_nodes_description_only"

# client.delete_collection(collection_name=collection_name)
client.create_collection(
    collection_name=collection_name,
    vectors_config=models.VectorParams(
        size=encoder.get_sentence_embedding_dimension(),
        distance=models.Distance.COSINE,
        on_disk=True
    ),
)


# Function to encode a batch of documents and upload
def encode_and_upload_batch(batch_data, batch_start_idx):
    batch_vectors = encoder.encode(
        [f"{doc['node_description']}" for doc in batch_data]
    ).tolist()

    points = [
        models.PointStruct(
            id=batch_start_idx + idx,
            vector=batch_vectors[idx],
            payload=doc
        )
        for idx, doc in enumerate(batch_data)
    ]

    # Upload batch to Qdrant
    client.upload_points(collection_name=collection_name, points=points)


# Batch processing
batch_size = 1000
for batch_start in range(0, len(data_list), batch_size):
    batch_data = data_list[batch_start:batch_start + batch_size]
    encode_and_upload_batch(batch_data, batch_start)
    print(f"Uploaded batch starting at index {batch_start}")

print("All data uploaded successfully.")


# Function to match user query with the vector embeddings
def match_query(client, encoder, collection_name, disease_name):
    hits = client.query_points(
        collection_name=collection_name,
        query=encoder.encode(disease_name).tolist(),
        limit=20,
    ).points
    return hits


results_name = match_query(client, encoder, "disease_nodes_names_only", "atopic dermatitis")
results_combined = match_query(client, encoder, "disease_nodes_all", "atopic dermatitis")

# for result in results:
#     print(result.payload, result.score)

# hidradenitis suppurativa



