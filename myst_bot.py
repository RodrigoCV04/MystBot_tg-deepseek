from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackContext, CallbackQueryHandler, ContextTypes, MessageHandler, PreCheckoutQueryHandler, filters
from telegram.constants import ChatAction
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, LabeledPrice, ShippingOption

#Model
from tools import ai_model as AI


TOKEN_BOT = "5339228187:AAGuhfopXOoILJ84Uv7NTz3tHOvUXMZ1XBw"
PAYMENT_PROVIDER_TOKEN = ""
WEB_APP_URL = "https://api-docs.deepseek.com/"

bot = telebot.TeleBot(TOKEN_BOT)

#Responses mold
#buttons array of InlineKeyboardButton
def SendResponseMold(chat_id, message:str , img_path:str="", buttons=[], markup_rows:int=0):
    markup = None
    if len(buttons) > 0 and len(buttons) > 0:
        markup_rows = markup_rows if markup_rows <= 3 else 3
        markup = InlineKeyboardMarkup(row_width=markup_rows)
        markup.add(*buttons)
    
    if img_path != "":
        bot.send_photo(chat_id=chat_id, caption=message, photo=img_path, reply_markup=markup, parse_mode='html')
    else:
        bot.send_message(chat_id=chat_id, text=message, reply_markup=markup, parse_mode='html')



#Call back handlers
async def CallbackHandlers(update: Update, ctx: CallbackContext):
    query = update.callback_query
    print(query)



#Commands
async def StartCommand(update: Update, ctx: CallbackContext):
    full_name = update.message.chat.full_name
    text = f'<a>Hola <b>{full_name}</b>! 👋\n \nBienvenido al chat con <b>MystBot</b>.</a>\n'
    text += f'<a>MystBot es un bot interactivo de inteligencia artificial en telegram 🤖</a>'
    buttons = [
        InlineKeyboardButton('Ayuda 🆘', callback_data='HelpMsg'),
        InlineKeyboardButton('Web 🌐', web_app=WebAppInfo(url=WEB_APP_URL))
    ]
    SendResponseMold(chat_id=update.message.chat_id, message=text, buttons=buttons, markup_rows=2)



async def TextHandler(update: Update, ctx: CallbackContext):
    bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)
    res = await AI.ChatModel(update.message.text)
    print(res)
    SendResponseMold(chat_id=update.message.chat_id, message=res)



def main():
    print('Running')
    app = ApplicationBuilder().token(TOKEN_BOT).build()
    app.add_handler(CommandHandler("start", StartCommand))
    app.add_handler(MessageHandler(filters.TEXT, TextHandler))
    app.add_handler(CallbackQueryHandler(CallbackHandlers))
    app.run_polling()


if __name__ == '__main__':
    main()