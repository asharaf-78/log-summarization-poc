from fastapi import FastAPI
from datamodels import ChatModel
from utility_functions import get_contex_from_documents,check_index_status,get_response
from starlette.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)



@app.get("/health")
def greet_message():
    return JSONResponse(
        status_code=200,
        content={"Response": "Application Root API Reached..."}
    )

@app.post("/services/log-summarization-agent/chat")
async def chat(question:ChatModel):
    try:
        index = check_index_status()
        context = get_contex_from_documents(index,question.query)
        response = get_response(context,question.query)
        return response
    except Exception as error:
        return {"Error":str(error)}
	