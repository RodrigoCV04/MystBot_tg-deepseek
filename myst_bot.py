from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, CallbackQueryHandler, ContextTypes, MessageHandler, PreCheckoutQueryHandler, filters
from telegram.constants import ChatAction
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, LabeledPrice, ShippingOption
import logging

#Model
from tools import ai_model as AI


TOKEN_BOT = "5339228187:AAGuhfopXOoILJ84Uv7NTz3tHOvUXMZ1XBw"
PAYMENT_PROVIDER_TOKEN = ""
WEB_APP_URL = "https://api-docs.deepseek.com/"

bot = telebot.TeleBot(TOKEN_BOT)


#Solo mostrar WARNINGS y ERRORES
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.WARNING
)


#Plantilla para enviar respuestas
#buttons: Arreglo de InlineKeyboardButton
def SendResponseTemplate(chat_id, message:str , img_path:str="", buttons:list[str]=[], markup_rows:int=0):
    markup = None
    if len(buttons) > 0 and len(buttons) > 0:
        markup_rows = markup_rows if markup_rows <= 3 else 3
        markup = InlineKeyboardMarkup(row_width=markup_rows)
        markup.add(*buttons)
    
    if img_path != "":
        return bot.send_photo(chat_id=chat_id, caption=message, photo=img_path, reply_markup=markup, parse_mode='html')
    else:
        return bot.send_message(chat_id=chat_id, text=message, reply_markup=markup, parse_mode='html')



#Callback handlers
def CallbackHandlers(update: Update, ctx: CallbackContext):
    query = update.callback_query
    callback = query.data
    chat_id = query.message.chat.id
    bot.answer_callback_query(callback_query_id=query.id)
    
    #Al presionar el botón Documentos
    if callback == 'file_query':
        file_path = "E:/Rod/Escuela/Universidad/SEM VI/Convocatoria_Movilidad.pdf"
        place_holder = SendResponseTemplate(chat_id=chat_id, message='Analizando 🤔').id
        res = AI.FileQuery('Que dice el documento?', file_path=file_path)
        bot.delete_message(chat_id=chat_id, message_id=place_holder)
        SendResponseTemplate(chat_id=chat_id, message=res)
        



#Comando start
async def StartCommand(update: Update, ctx: CallbackContext):
    full_name = update.message.chat.full_name
    text = f'<a>Hola <b>{full_name}</b>! 👋\n \nBienvenido al chat con <b>MystBot</b>.</a>\n'
    text += f'<a>MystBot es un bot interactivo de inteligencia artificial en telegram 🤖</a>'
    buttons = [
        InlineKeyboardButton('Documento 📄', callback_data='file_query'),
        InlineKeyboardButton('Web 🌐', web_app=WebAppInfo(url=WEB_APP_URL))
    ]
    SendResponseTemplate(chat_id=update.message.chat_id, message=text, buttons=buttons, markup_rows=2)



##Interacción sin contexto ni db
async def TextHandler(update: Update, ctx: CallbackContext):
    chat_id = update.message.chat_id
    bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
    res = AI.ChatModel(query=update.message.text, prompt='Responder brevemente con 150 tokens')
    SendResponseTemplate(chat_id=chat_id, message=res)



#Interacción con contexto y db
def ContextChat(db, memory, prompt):
    async def TextContextHandler(update: Update, ctx: CallbackContext):
        chat_id = update.message.chat_id
        place_holder = SendResponseTemplate(chat_id=chat_id, message='Pensando... 🤔').id
        res = AI.DBQueryMemory(db=db, query=update.message.text, memory=memory, prompt=prompt)
        bot.delete_message(chat_id=chat_id, message_id=place_holder)
        SendResponseTemplate(chat_id=chat_id, message=res)
    return TextContextHandler



def main():
    docs = AI.SplitFile('E:/Rod/Escuela/Universidad/SEM VI/Convocatoria_Movilidad.pdf')
    db = AI.CreateDB(docs=docs)
    memory = AI.ConversationMemory()
    prompt = AI.PromptTemplate(prompt="Eres un asistente cordial. Si el usuario saluda, agradece o hace una pregunta general, responde sin usar el documento. Si la pregunta es técnica o relacionada con el contenido, responde usando el contexto.")
    
    app = ApplicationBuilder().token(TOKEN_BOT).build()
    app.add_handler(CommandHandler("start", StartCommand))
    app.add_handler(MessageHandler(filters.TEXT, ContextChat(db=db, memory=memory, prompt=prompt)))
    app.add_handler(CallbackQueryHandler(CallbackHandlers))
    print('Running')
    app.run_polling()



if __name__ == '__main__':
    main()