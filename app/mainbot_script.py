from config import API_TOKEN
import telebot
from telebot import apihelper

bot = telebot.TeleBot(token=API_TOKEN)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = f"Hello , {message.from_user.first_name} , welcome to MuseTwinDate!"
    bot.send_message(chat_id=message.chat.id, text=welcome_text)

@bot.message_handler(commands=['help'])
def send_help(message):
    list_of_commands = {
        "/start" : "Welcome to user",
        "/help" : "Describe every commands to user",
        "/app" : "Starting application",
        "/premium" : "Here you can buy premium status",
    }
    help_menu = f"Here is list of commands: {[key for key,value in list_of_commands.items()]}"
    bot.send_message(chat_id=message.chat.id, text=help_menu)

@bot.message_handler(commands=['premium'])
def premium(message):
    list_of_premium = {

    }

bot.polling()

