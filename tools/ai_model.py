import asyncio
from langchain_deepseek import ChatDeepSeek

DEEPSEEK_KEY = "sk-7b3c7cf39b354e1b8ba5258f633e8b94"
MODEL = "deepseek-chat"

async def ChatModel(text: str) -> str:
    llm = ChatDeepSeek(api_key=DEEPSEEK_KEY, model=MODEL)
    res = await asyncio.to_thread(llm.invoke, f'Responder brevemente con 150 tokens: {text}')
    return res.content


async def main():
    respuesta = await ChatModel("Hola!!")
    print(respuesta)

if __name__ == '__main__':
    asyncio.run(main())
