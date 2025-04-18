from neo4j import GraphDatabase


def get_neo4j_driver() -> GraphDatabase.driver:
    URI = "neo4j://robokopkg.renci.org:7687"
    AUTH = ("", "")
    driver = GraphDatabase.driver(uri=URI, auth=AUTH)
    return driver


def fetch_data_from_neo4j(query: str):
    # Get the driver instance
    driver = get_neo4j_driver()

    # Open a new session
    with driver.session() as session:
        # Run the Cypher query
        result = session.run(query)

        # Extract the data from the result
        data = [record.data() for record in result]

    # Close the driver connection
    driver.close()
    return data

