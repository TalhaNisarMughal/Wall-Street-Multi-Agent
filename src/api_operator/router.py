import json, os, time
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from dotenv import load_dotenv
from src.utils.db import PGDB
from pathlib import Path

router = APIRouter()
db = PGDB()
ROOT_DIR = Path.cwd()
STORAGE_FILE = os.path.join(ROOT_DIR,"src/state_management/bot_query.json")
load_dotenv()

class QueryRequest(BaseModel):
    bot_query: str
    
@router.get('/health_check')
async def index_page():
    return {"message": "Operator BOT Heath Success"}


@router.post('/operator/get_response')
async def generate_operator_response(
        request: QueryRequest

):
    bot_query = request.bot_query
    print(bot_query)
    """
    This endpoint is used to interact with the SOT chatbot and will respond to user query

    Args:
        bot_query (str, required): _description_. 
        - Defaults to Body("Hello").

    """

    try:
        print("I am hit")
        # Write the bot query to the JSON file
        with open(STORAGE_FILE, "w") as file:
            json.dump({"bot_query": bot_query}, file)
        i = 0
        file_path = os.path.join(ROOT_DIR, "src/state_management/operator_response.json")
        while i < 10:
            if os.path.exists(file_path):
                with open(file_path, 'r') as json_file:
                    file = json.load(json_file)
                    operator_response = file["operator_response"]
                    if operator_response:
                        print("response received")
                        return operator_response
                    else:
                        time.sleep(6)
                        i+=1
                        response = ""
        return response   
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    
    