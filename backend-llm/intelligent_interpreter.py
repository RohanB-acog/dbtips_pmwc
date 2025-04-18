
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
import os

api_key =os.getenv('OPENAI_API_KEY')


def intelligent_interpreter(model: str, tool_input: str, observation: str) -> str:
    """
        This method receives the observation from the python tool if there's any error in code execution.
        It then sends the error to "gpt-3.5-turbo" and gets a feed back on the error.
        The purpose is to give a nice precise and detailed feedback back to GPT-4.
    """

    template: str = """
        You are a python coding assistant. You will be given a code and the output(if any errors) after execution. 
        Your job is to provide a precise and helpful feedback. The feedback should be just under 20 words.
        
         Example 1:
        Code:
        adata.uns['B cells_before_vs_after_deseq2_res'].index[adata.uns['B cells_before_vs_after_deseq2_res'].pvalue < 0.05]

        Python_interpreter_output:
        KeyError: 'B cells_before_vs_after_deseq2_res'

        Feedback:
        The key error is because the key 'B cells_before_vs_after_deseq2_res' does not exist in the dictionary.
        You can check if the key exists before accessing it using `adata.uns`

        Example 2:
        Code:
        adata.obs.refs_harmonized.str.contains('B cells').sum()/adata.obs.n_obs.sum()
        
        Python_interpreter_output:
        AttributeError: 'DataFrame' object has no attribute 'n_obs'

        Feedback:
        The code is trying to calculate the percentage of B cells in the dataset. 
        However, it is encountering an error due to the absence of the 'n_obs' attribute in the DataFrame.

        Code:
        {tool_input}

        Output:
        {observation}

        Feedback:
    """
    prompt = PromptTemplate(template=template, input_variables=["tool_input", "observation"])
    # llm = OpenAI(model_name="Mistral-7B-v0.1", openai_api_key="NULL", openai_api_base="https://aganitha-llm.own1.aganitha.ai/v1", temperature=0)
    llm = ChatOpenAI(model_name=model, temperature=0, openai_api_key=api_key)
    # print("Hello")
    llm_chain = LLMChain(prompt=prompt, llm=llm)
    intelligent_observation = llm_chain.run({'tool_input': tool_input, 'observation': observation})
    # print(observation)
    return intelligent_observation
