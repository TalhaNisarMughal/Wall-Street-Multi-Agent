import os, openai, json, requests
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain.memory import ConversationBufferWindowMemory
from src.Chatbot import prompt_templates
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain.schema.document import Document
from langchain_community.vectorstores import Chroma
from langchain.chains.openai_functions import create_structured_output_runnable
from src.models.models import Route
from dotenv import load_dotenv
from src.utils.db import PGDB

load_dotenv()

class Bot():
    
    def __init__(self):
        
        self.root_dir = Path.cwd()
        os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
        self.embedding = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
        self.MODEL_NAME = os.getenv("MODEL_NAME_B")
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.llm_api = openai.OpenAI(api_key=openai.api_key)
        # self.refine_llm = ChatOpenAI(model=os.getenv('MODEL_NAME_B'), temperature=0)
        # self.router_llm = ChatOpenAI(model=os.getenv('MODEL_NAME_B'), temperature=0)
        
        #### Chroma DB Retriever
        self.chromadb_dir = os.path.join(self.root_dir, "ChromaDB")
        chroma_db = Chroma(collection_name="proposal", persist_directory=self.chromadb_dir,
                  embedding_function=self.embedding)
        self.chroma_db_retriever = chroma_db.as_retriever(
            search_kwargs={
                'k': 5
                }
            )
        
        #### Chains
        # self.refined_query_chain = self.__get_refine_query_chain()
        # self.router_chain = self.__get_router_chain()
        
        ### State management
        self.global_dictionary_to_manage_state = {}
        self.db = PGDB()
    
    @staticmethod
    def extract_memory_from_history(history):
        memory = ""
        for message in history:
            memory += f"Human: {message[1]}\nAI: {message[2]}\n"
        return memory
    
    def __get_chat_history(self, user_id):

        history = self.db.fetch_chat_history(user_id)
        memory = self.extract_memory_from_history(history[-5:])

        return memory
    
    #### Refine Query Chain #####
    def __get_refine_query_chain(self):
        prompt = PromptTemplate.from_template(template=prompt_templates.REFINE_QUERY_PROMPT)
        chain = prompt | self.refine_llm 

        return chain
    
    def get_refined_respones(self, query , history):
        
        response = self.refined_query_chain.invoke(
                {"conversation_history": history,
                 "userPrompt": query
                 })
        
        return response.content
    
    def __get_router_chain(self):
        main_retrievers_info = ""
        for i in prompt_templates.router_desc:
            main_retrievers_info += f'{i["category"]}:{i["description"]}\n'
        template_main_router = prompt_templates.ROUTER_TEMPLATE + f"""\n{main_retrievers_info}\n\n"""
        template_second_half = "<< INPUT >>\n{input}\n\n<< OUTPUT >>\n"
        template_main_final = template_main_router + template_second_half
        template = PromptTemplate(template=template_main_final, input_variables=["input"])

        chain = create_structured_output_runnable(Route,
                                                  self.router_llm ,
                                                  template)

        return chain
    
    ### Context Retriever ###
    def __get_relevant_content_from_db(self, query) -> list[Document]:
        """
        Get relevant content from the sementic database
        :param query:
        :param is_authorized:
        :return:  list[Document]
        """
        relevant_content = self.chroma_db_retriever.get_relevant_documents(query)

        return relevant_content
    
    ### Prompt Manager ###
    def __get_system_prompt(self, context, history):
        
        template_inputs = f"""
context:
``{context}``

chat history:
`{history}`
"""
        system_prompt = f"""{prompt_templates.PROMPT}\n{template_inputs}"""
        return system_prompt
    
    def __get_default_system_prompt(self, history):

        template_inputs = f"""

chat history:
`{history}`
"""
        system_prompt = f"""{prompt_templates.DEFAULT_RESPONSE_GENERATION_PROMPT}\n{template_inputs}"""
        
        return system_prompt
    def __get_pre_classifier(self, context, user_query):
        template_inputs = f"""

context:
``{context}``

user_query:
`{user_query}`
"""
        system_prompt = f"""{prompt_templates.PRE_CLASSIFIER_PROMPT}\n{template_inputs}"""
        
        return system_prompt
    
    def verify_relevancy_of_query_with_context(self, query, context):
        prompt = self.__get_pre_classifier(
                context=context, 
                user_query=query
            )
        
        messages = [
            {
                "role": "system", 
                "content": prompt
             },
            {
                "role": "user", 
                "content": query
            }
        ]
        
        response = self.llm_api.chat.completions.create(
            model=self.MODEL_NAME,
            messages=messages
        )
        status = response.choices[0].message.content
        
        print("Status: ", status)
        return status
    
    def get_rephrased_query(self, query):
        
        messages = [
            {
                "role": "system", 
                "content": prompt_templates.QUERY_RE_FACTOR_PROMPT
             },
            {
                "role": "user", 
                "content": query
            }
        ]
        
        response = self.llm_api.chat.completions.create(
            model=self.MODEL_NAME,
            messages=messages
        )
        query = response.choices[0].message.content
        
        print("Status: ", query)
        return query
    
    @staticmethod
    def get_operator_response(bot_query):
        endpoint = os.getenv('LOCALHOST_OPERATOR_API_URL')
        payload = {
            "bot_query": bot_query,
        }
        
        response = requests.post(endpoint, json=payload)
        if response.status_code == 200:
            
            return response
        else:
            print(response)
            raise Exception ("Could not send request to %s" % endpoint)
            
    ### Chatbot Response Generation Function ###
    def get_query_response(self, query, user_id: str = ''):
        """
        Get RAG (Retrieval-Augmented Generation) response from the LLM for user question.

        :param query: str: The user's query string.
        :param is_authorized: bool: A flag indicating if the user is authorized.
        :return: Streamed response
            - Memory object of type ConversationBufferWindowMemory
        """
        memory = self.__get_chat_history(user_id)
        
        # refined_query = self.get_refined_respones(query,str(memory) )
        # refined_query = refined_query.lower().replace("refined query:", '')
        self.global_dictionary_to_manage_state["user_query"] = query
        self.global_dictionary_to_manage_state["refine_query"] = query
        self.global_dictionary_to_manage_state["memory"] = memory
        
            
        context = self.__get_relevant_content_from_db(query)
        print(len(context))
        
        status = self.verify_relevancy_of_query_with_context(query, context)
        
        if status == "known":
            prompt = self.__get_system_prompt(
                    context=context, 
                    history=memory
                )

            self.global_dictionary_to_manage_state["context"] = str(context)
            
            messages = [
                {
                    "role": "system", 
                    "content": prompt
                },
                {
                    "role": "user", 
                    "content": query
                }
            ]
            
            response = self.llm_api.chat.completions.create(
                model=self.MODEL_NAME,
                messages=messages,
                # stream=True,
            )
            
            response = response.choices[0].message.content
        else:
            self.global_dictionary_to_manage_state["context"] = str(context)
            rephrased_query = self.get_rephrased_query(query)
            
            response = rephrased_query
            try:
                response = self.get_operator_response(str(rephrased_query))
                if response == "":
                    response = "I am not able to respond this query at this time."
            except Exception as e:
                print(e)
                
        ### State Management ###
        state_management_directory = os.path.join(self.root_dir, "state_management")
        if not os.path.exists(state_management_directory):
            os.makedirs(state_management_directory)
        
        with open(os.path.join(state_management_directory, "state_management_dictionary.json"), 'w') as json_file:
            json.dump(self.global_dictionary_to_manage_state, json_file, indent=4) 
        response = response.replace('"', '')
        
        return response, memory, context