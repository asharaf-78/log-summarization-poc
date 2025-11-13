import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
import re
from typing import List
from langchain_core.documents import Document
from Utilities.llmUtils import get_databricks_chatmodel
from Utilities.prompts import raw_prompt
from Utilities.utilities_functions import check_index_status
from langchain_core.output_parsers import JsonOutputParser
from databricks.vector_search.reranker import DatabricksReranker 
from langchain_core.prompts import ChatPromptTemplate


def convert_vector_search_to_documents(results) -> List[Document]:
    column_names = [col["name"] for col in results["manifest"]["columns"]]
    langchain_docs = []
    for item in results["result"]["data_array"]:
        metadata = {}
        for idx, field in enumerate(item[1:-1], start=1): 
            metadata[column_names[idx]] = field
        metadata["file_name"]
        doc = Document(
            page_content=metadata["page_content"],  
            metadata={"filename":metadata["file_name"]}
        )
        langchain_docs.append(doc)

    return langchain_docs

def get_context_from_documents_idmc(user_query:str,index)-> List[dict]:

    """
        This tool retrieves semantically similar documents from the Databricks vector store based on the user's query. 
        After fetching the relevant documents, it re-ranks them to enhance augmentation quality and returns the refined results.

        Input:
        user_query: The text query provided by the user.

        Output:
        A list of dictionaries, where each dictionary contains:
        filename: The source document from which the information was retrieved.
        page_content: The extracted content relevant to the query
    
    """
    try:
        results = index.similarity_search(
            query_text=user_query,
            columns=["id", "page_content","file_name"],
            num_results=10,
            query_type="hybrid",
            reranker=DatabricksReranker(columns_to_rerank=["page_content"])
            )
        similar_docs = convert_vector_search_to_documents(results)
        context = []
        pattern = r",|=|-->|\.{3}|\*|\.|^\s*$"
        for item in similar_docs:
            doc = {}
            filename = item.metadata["filename"]
            page_content = re.sub(pattern, "", item.page_content, flags=re.MULTILINE)
            doc["filename"] = filename
            doc["page_content"] = page_content
            context.append(doc)
        return context
    
    except Exception as error:
        return error
    
def get_response_idmc(context:List[dict],user_query:str)->dict:
    """
        This tool generates a response from the LLM based on the user's query and the contextual information retrieved 
        through a similarity search.

        Input:
        context: A list of dictionaries containing:
            filename: The source document from which the context was retrieved.
            page_content: The relevant extracted content.
        user_query: The user's question.

        Output:
        The LLM-generated response.
    """
    try:
        model = get_databricks_chatmodel() 
        prompt = ChatPromptTemplate.from_template(template = raw_prompt)
        chain  = prompt | model | JsonOutputParser()
        response = chain.invoke({"query":user_query,"context":context})
        return response
    except Exception as error:
        raise error
    
# if __name__=='__main__':
#     query = "What is Invalid symbol reference Lead_Id? How to fix it?"
#     context = get_context_from_documents_idmc(query)
#     response = get_response_idmc(context,query)
#     print(response)

    

    
    
