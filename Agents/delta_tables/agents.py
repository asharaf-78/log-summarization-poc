import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from databricks import sql
from dotenv import load_dotenv 
from Utilities.llmUtils import get_databricks_chatmodel
from Utilities.prompts import structured_prompt
from langchain_core.prompts import ChatPromptTemplate
from Utilities.datamodels import QueryOutput

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


def get_sql_query_and_references(query:str)->dict:
    """This function is used to generate spark-sql query and references based on users question.""" 
    try:
        prompt = ChatPromptTemplate.from_template(template = structured_prompt)
        model = get_databricks_chatmodel().with_structured_output(QueryOutput)
        chain = prompt | model
        response = chain.invoke({"top_k":5,"table_info":get_table_details(),"input":query}) 
        return response
    except Exception as error:
        raise error

def execute_query(sql_query:str):
    try:
        connection = get_connection()
        cursor = connection.cursor() 
        response = cursor.execute(sql_query)
        return response.fetchall()
    except Exception as error:
        raise error
    finally:
        connection.close()
        cursor.close()

def generate_answer(query,sql_query,result)-> dict:
    """Answer question using retrieved information as context."""
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
#     query ="How many job has been failed for today? out of all job run for today?"
#     response = get_sql_query_and_references(query)
#     sql_query,references = response.query,response.references
#     answer = execute_query(sql_query)
#     result = generate_answer(query,sql_query,answer)
#     result["references"] = references
#     print(result)



