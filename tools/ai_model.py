import asyncio
from langchain_deepseek import ChatDeepSeek
from langchain_unstructured import UnstructuredLoader
#from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import  RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import FAISS


DEEPSEEK_KEY = "sk-7b3c7cf39b354e1b8ba5258f633e8b94"
MODEL = "deepseek-chat"

async def ChatModel(text: str) -> str:
    llm = ChatDeepSeek(api_key=DEEPSEEK_KEY, model=MODEL)
    res = await asyncio.to_thread(llm.invoke, f'Responder brevemente con 150 tokens: {text}')
    return res.content


async def LoadFile(file_url:str):
    try:
        loader = UnstructuredLoader(file_path=file_url)
        pages = await asyncio.to_thread(loader.load)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        text_splitter.split_documents(pages)
        print(text_splitter)
        return text_splitter
    except Exception as e:
        print(f'ERR: Could not read the file \n{e}')
        return None


def CreateDB(docs):
    embeddings = HuggingFaceBgeEmbeddings()
    db = FAISS.from_documents(documents=docs, embedding=embeddings)
    db.save_local('deepseek_db')
    return db


async def main():
    respuesta = await LoadFile("C:/Users/cesar/Downloads/Grupos_SEM_2024-2.xlsx")
    #print(respuesta)

if __name__ == '__main__':
    asyncio.run(main())
