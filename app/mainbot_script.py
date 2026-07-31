from config import API_TOKEN
import telebot
from telebot import apihelper

bot = telebot.TeleBot(token=API_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = f"Hello , {message.from_user.first_name} , welcome to MuseTwinDate!"
    bot.send_message(chat_id=message.chat.id, text=welcome_text)

bot.polling()