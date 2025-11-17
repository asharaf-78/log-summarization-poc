import os
import sys,json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from databricks import sql
from dotenv import load_dotenv 
from Utilities.llmUtils import get_databricks_chatmodel
from Utilities.prompts import structured_prompt
from langchain_core.prompts import ChatPromptTemplate
from Utilities.datamodels import QueryOutput
from langchain_core.tools import tool
from langchain.agents import create_agent

load_dotenv()

def get_connection():
    "This tool takes a sql query and execute it and return the result."
    try:
      connection = sql.connect(server_hostname   = os.getenv("DATABRICKS_SERVER_HOSTNAME"),
                    http_path = os.getenv("DATABRICKS_HTTP_PATH"),
                    access_token = os.getenv("DATABRICKS_TOKEN"))
      return connection
    except Exception as error:
        raise error
            
def get_table_details():
    "Use this tool to get the information about columns and datatypes of a tables"

    catalog = os.getenv("DATABRICKS_CATALOG")
    databricks_schema = os.getenv("DATABRICKS_SCHEMA")
    try:
        connection = get_connection() 
        cursor = connection.cursor()
        tables = os.getenv("TABLES").split(",")
        tables_with_schemas = []
        for table in tables:
            response = {}
            tbl = f"{catalog}.{databricks_schema}.{table}"
            query = f"describe table {tbl}"
            response["table"] = tbl
            result = cursor.execute(query)
            schema = []
            for row in result:
                if row.data_type=='':
                    break
                schema.append((row.col_name,row.data_type))

            response["schema"] = schema 
            tables_with_schemas.append(response)
        
        return tables_with_schemas
    
    except Exception as error:
        raise error
    finally:
        connection.close()
        cursor.close()

@tool
def get_sql_query_and_references(query:str)->dict:
    """
    Convert a natural-language request into a valid Spark SQL query and return
    the tables referenced in that query.

    Input : A User's query.
    Output: A valid spark-sql query with referenced table  
       
    """ 
    try:
        prompt = ChatPromptTemplate.from_template(template = structured_prompt)
        model = get_databricks_chatmodel().with_structured_output(QueryOutput)
        chain = prompt | model
        response = chain.invoke({
                    "table_info":get_table_details(),
                    "input":query
                }) 
        return response
    except Exception as error:
        raise error
@tool
def execute_query(sql_query:str):
    "This function is used to execute the spark-sql query and return the result."
    try:
        connection = get_connection()
        cursor = connection.cursor() 
        response = cursor.execute(sql_query)
        return response.fetchall()
    except Exception as error:
        print(error)
    connection.close()
    cursor.close()

@tool
def generate_answer(query,sql_query,result)-> dict:
    """
    Generate a natural-language answer using the user query, the Spark SQL query,
    and the SQL result as context.
    Returns a dict with:
      - 'response': the final answer generated from the provided context.
    """
    try:
        prompt = (
            "Given the following user question, corresponding SPARK-SQL query, "
            "and SPARK SQL result, answer the user question as accurate as possible. \n\n"
            f"Question: {query}\n"
            f"SQL Query: {sql_query}\n"
            f"SQL Result: {result}"
        )
        model = get_databricks_chatmodel()
        response = model.invoke(prompt).content
        answer={}
        answer["response"] = response
        return answer
    
    except Exception as error:
        raise error



# if __name__=='__main__':
#     query ="Can you list top 5 jobs which took highest time on 14-Nov 2025?"
#     agent = create_agent(model=get_databricks_chatmodel(),
#                          tools=[get_sql_query_and_references,execute_query,generate_answer],
#                          system_prompt = structured_prompt
#                          )
#     result = agent.invoke(
#         {"messages": [{"role": "user", "content": query}]}
#     )
#     response = json.loads(result["messages"][-1].content)
#     print(response)




