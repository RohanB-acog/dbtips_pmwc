from langchain_community.chat_models import ChatPerplexity
from langchain_core.prompts import ChatPromptTemplate
from langchain.tools import tool
import os

prplx_key=os.getenv('PERPLEXITY_KEY')

@tool
def access_web(query: str):
    """
    Access the internet to retrieve relevant data or perform searches based on the user query. 
    This tool is powered by an LLM, which can intelligently process queries, extract information, 
    and summarize content from the provided sources.

    Parameters:
        query (str): The user query that contains a single or multiple URLs or online sources to fetch data from. 
                    
        Examples include: 
        - Summarize the key findings discussed in the URLs 'https://example1.com', 'https://example2.com'.
        - Can you summarize the key findings from these studies on the role of IL-6 in inflammation and its implications for autoimmune diseases? https://pubmed.ncbi.nlm.nih.gov/12345678/ https://pubmed.ncbi.nlm.nih.gov/87654321/

    Returns:
        str: A summary of the retrieved information or an error message if the request fails.
    """
    # ChatPerplexity setup
    chat = ChatPerplexity(
        temperature=0.5,
        pplx_api_key=prplx_key,
        model="sonar",
        max_tokens=4096
    )
    system = "You are a helpful assistant. Be precise and concise."
    human = "{input}"
    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])

    # Create chain
    chain = prompt | chat

    # Invoke the chain with the user input
    response = chain.invoke({"input": query})
    return response.content