import os
from dotenv import load_dotenv
from databricks_langchain import ChatDatabricks

load_dotenv()

endpoint = os.getenv("ENDPOINT_NAME")
host = os.getenv("DATABRICKS_HOST") 
token = os.getenv("DATABRICKS_TOKEN")

def get_databricks_chatmodel():
    chat_model = ChatDatabricks(endpoint=endpoint,disable_notice=True)
    return chat_model

# if __name__=='__main__':
#     model = get_databricks_chatmodel()
#     response = model.invoke("Hello")
#     print(response)

