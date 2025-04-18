from neo4j import GraphDatabase

def get_neo4j_driver() -> GraphDatabase.driver:
    URI = "neo4j://robokopkg.renci.org:7687"
    AUTH = ("", "")
    driver = GraphDatabase.driver(uri=URI, auth=AUTH)
    return driver