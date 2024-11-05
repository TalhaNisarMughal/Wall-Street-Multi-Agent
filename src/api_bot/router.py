from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from src.Chatbot.bot import Bot
from dotenv import load_dotenv
from src.utils.db import PGDB
from operator_app import get_operator_response

router = APIRouter()
bot = Bot()
db = PGDB()
load_dotenv()

class Message(BaseModel):
    content: str
    
@router.get('/health_check')
async def index_page():
    return {"message": "BOT Heath Success"}

@router.post('/bot/generate_response')
async def generate_query_response(
        user_query: str = Body("Hello"),
        user_id: str = Body(''),

):
    """
    This endpoint is used to interact with the SOT chatbot and will respond to user query

    Args:
        user_query (str, required): _description_. 
        - Defaults to Body("Hello").
        
        uuid (str, required): _description_.
        - Unique User ID. Default to Body("").
    """


    try:
        print("First hit")
        response, memory, context = bot.get_query_response(
            query=user_query,
            user_id=user_id,
        )
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    
    # def generate(memory):
    #     content = ''
    #     for chunk in response:
    #         if chunk.choices[0].delta.content:
    #             content += chunk.choices[0].delta.content
    #             yield chunk.choices[0].delta.content
    #         else:
    #             pass
        
    data_to_insert = (
        user_id, user_query, response, str(context), memory 
    )
    db.insert_chat_history_in_table(data_to_insert)
    
    return response

    # headers = {'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache',
    #            'X-Accel-Buffering': 'no'}
    # return StreamingResponse(generate(memory), media_type="text/event-stream", headers=headers)
    
@router.post('/operator/get_response')
async def generate_operator_response(
        bot_query: str = Body("Hello")

):
    """
    This endpoint is used to interact with the SOT chatbot and will respond to user query

    Args:
        user_query (str, required): _description_. 
        - Defaults to Body("Hello").
        
        uuid (str, required): _description_.
        - Unique User ID. Default to Body("").
    """


    try:
        print("I am hit")
        # response = "HEhehehehehe"
        response = get_operator_response(
            bot_query=bot_query,
        )
        print("response received")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))
    
    return response