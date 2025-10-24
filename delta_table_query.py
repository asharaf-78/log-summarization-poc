import os
from databricks import sql
from dotenv import load_dotenv 
from llmUtils import get_databricks_chatmodel
from idmc_prompt import structured_prompt
from langchain.prompts import ChatPromptTemplate
from datamodels import QueryOutput
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

def get_connection():
    "This tool takes a sql query and execute it and return the result."

    connection = sql.connect(server_hostname   = os.getenv("DATABRICKS_SERVER_HOSTNAME"),
                    http_path = os.getenv("DATABRICKS_HTTP_PATH"),
                    access_token = os.getenv("DATABRICKS_TOKEN"))
            
    return connection
        
def get_table_details():
    "Use this tool to get the information about columns and datatypes of a table"

    catalog = os.getenv("DATABRICKS_CATALOG")
    schema = os.getenv("DATABRICKS_SCHEMA")
    try:
        connection = get_connection() 
        cursor = connection.cursor()
        tables = os.getenv("TABLES").split()
        tables_with_schemas = []
        for table in tables:
            response = {}
            tbl = f"{catalog}.{schema}.{table}"
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
        print(error)
        raise error
    finally:
        connection.close()
        cursor.close()


def get_sql_query(query:str)->str: 

    prompt = ChatPromptTemplate.from_template(template = structured_prompt)
    model = get_databricks_chatmodel().with_structured_output(QueryOutput)
    chain = prompt | model
    response = chain.invoke({"top_k":5,"table_info":get_table_details(),"input":query}) 
    return response.query 

def execute_query(sql_query:str):
    try:
        connection = get_connection()
        cursor = connection.cursor() 
        response = cursor.execute(sql_query)
        return response.fetchall()
    except Exception as error:
        print(error)
        raise error
    finally:
        connection.close()
        cursor.close()

def generate_answer(query,sql_query,result):
    """Answer question using retrieved information as context."""
    prompt = (
        "Given the following user question, corresponding SQL query, "
        "and SQL result, answer the user question.\n\n"
        f"Question: {query}\n"
        f"SQL Query: {sql_query}\n"
        f"SQL Result: {result}"
    )
    model = get_databricks_chatmodel() | StrOutputParser()
    response = model.invoke(prompt)
    return response

if __name__=='__main__':
    query = "How many jobs has been failed in lat week?"
    sql_query = get_sql_query(query)
    answer = execute_query(sql_query)
    response = generate_answer(query,sql_query,answer)
    print(response)



