import os
import sys,json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from dotenv import load_dotenv
from fastapi import FastAPI
from Utilities.datamodels import ChatModel
from starlette.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langchain.agents import create_agent
from Utilities.prompts import structured_prompt
from Utilities.llmUtils import get_databricks_chatmodel
from databricks.vector_search.client import VectorSearchClient 
from Utilities.utilities_functions import get_confindence_score,get_follow_up_questions
from Agents.airflow_agent.agent import get_context_from_documents_airflow,get_response_airflow
from Agents.idmc_agent.agent import get_context_from_documents_idmc,get_response_idmc
from Agents.delta_tables.agents import get_sql_query_and_references,execute_query,generate_answer

load_dotenv() 

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app = FastAPI(root_path="/services/log-summarization-agent")

@app.get("/health")
def greet_message():
    return JSONResponse(
        status_code=200,
        content={"Response": "Application Root API Reached..."}
    )

@app.post("/chat")
async def chat(chat:ChatModel):
    try:
        question = chat.query 
        query_type = chat.platform_type
        client = VectorSearchClient(disable_notice=True)
        if query_type.lower()=='s3':
            index_name = os.getenv("DATABRICKS_IDMCLOGS_INDEX")
            index = client.get_index(index_name=index_name)
            context = get_context_from_documents_idmc(question,index)
            response = get_response_idmc(context,question)
        elif query_type.lower()=='cloudwatch':
            index_name = os.getenv("DATABRICKS_AIRFLOWLOGS_INDEX")
            index = client.get_index(index_name=index_name)
            context = get_context_from_documents_airflow(question,index)
            response = get_response_airflow(context,question)
        elif query_type.lower()=='delta_table':
            agent = create_agent(model=get_databricks_chatmodel(),
                         tools=[get_sql_query_and_references,execute_query,generate_answer],
                         system_prompt = structured_prompt
                         )
            result = agent.invoke(
                {"messages": [{"role": "user", "content": question}]}
            )
            response = json.loads(result["messages"][-1].content)
        else:
            return {"Error":"Please enter correct platform type from ['s3','cloudwatch','delta_table']"}
         
        response["follow-up-questions"] = get_follow_up_questions(question,response["response"])
        response["confidence_score"] = get_confindence_score(question,response["response"])
        return response
    except Exception as error:
        return {"Error":str(error)}
	