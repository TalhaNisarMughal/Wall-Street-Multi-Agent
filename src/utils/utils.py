import os
import chromadb
import pdfplumber
from langchain.schema.document import  Document
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class CreateVectorStore():
    
    def __init__(self) -> None:
        
        os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
        self.embedding = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
        self.ROOT_DIR = "../../"
        self.chromadb_dir = os.path.join(self.ROOT_DIR, "ChromaDB")
        self.collection_name = 'proposal'

        
    def store_data_in_chromadb(self, documents):
        
        try:
            chroma_client = chromadb.Client()
            chroma_client.create_collection(name=self.collection_name)
            db = Chroma.from_documents(documents, self.embedding, collection_name=self.collection_name, persist_directory=self.chromadb_dir)
            db.persist()
            print("Data stored successfully in ChromaDB.")
            
        except Exception as e:
            print(e)
    
    def extract_text_and_images_from_pdf(self, pdf_file):
        text_data = []
        with pdfplumber.open(pdf_file) as pdf:
            for i, page in enumerate(pdf.pages):
                metadata = {}
                text = ""
                page_number = i + 1
                
                page_text = page.extract_text() or ""
                text += page_text 
                text = text.replace(f"{page_number}", '')
                    
                metadata["page_number"] = page_number
                document = Document(page_content=text,metadata=metadata)
                text_data.append(document)

        return text_data
    
if __name__ == "__main__":
    
    obj = CreateVectorStore()
    pdf_path = '../../data/Proposal for buildersapp.pdf'
    
    documents_list = obj.extract_text_and_images_from_pdf(pdf_path)

    obj.store_data_in_chromadb(documents_list)