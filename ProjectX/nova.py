import json
import os

import telebot
from google import genai


BOT_TOKEN = "8334134153:AAFLbkPFNIOrjBdXjgQG8UFn5g8Pygxrm2Y"
GEMINI_API_KEY = "AIzaSyBp-i5_GmVYiuhpSMK5XtBE3dZB4eI68_0"

MAX_CHARS_REQUEST = 5000
MAX_TELEGRAM_CHARS = 4000
HISTORY_FILE = "chat_history.json"
MAX_CONTEXT_MESSAGES = 5


bot = telebot.TeleBot(BOT_TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("Ошибка декодирования JSON. Возвращается пустая история.")
                return {}
    return {}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

chat_history = load_history()


def format_text_for_telegram(raw_text):

    text = raw_text

    text = text.replace('***', '').replace('__*', '').replace('__', '')

    paragraphs = [p.strip() for p in text.split("\n") if p.strip() != ""]

    if not paragraphs:
        return ""

    paragraphs[0] = f"📚 {paragraphs[0]}"


    formatted_text = "---\n\n" + "\n\n".join(paragraphs) + "\n\n---"

    return formatted_text

def send_long_message(chat_id, text):
    for i in range(0, len(text), MAX_TELEGRAM_CHARS):
        bot.send_message(chat_id, text[i:i + MAX_TELEGRAM_CHARS], parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_text = message.text
    chat_id = str(message.chat.id)

    if len(user_text) > MAX_CHARS_REQUEST:
        bot.reply_to(message, f"Ваш запрос слишком длинный! Пожалуйста, сократите его до {MAX_CHARS_REQUEST} символов.")
        return

    context_text = ""
    if chat_id in chat_history:
        last_messages = chat_history[chat_id][-MAX_CONTEXT_MESSAGES:]
        for msg in last_messages:
            user_msg = str(msg.get('user', ''))
            bot_msg = str(msg.get('bot', ''))
            context_text += f"User: {user_msg}\nBot: {bot_msg}\n"

    context_text += f"User: {user_text}\nBot:"

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=context_text
        )

        bot_reply = response.text


        formatted_reply = format_text_for_telegram(bot_reply)


        send_long_message(message.chat.id, formatted_reply)


        if chat_id not in chat_history:
            chat_history[chat_id] = []

        chat_history[chat_id].append({"user": user_text, "bot": formatted_reply})
        save_history(chat_history)

    except Exception as e:
        error_message = str(e)
        if "RESOURCE_EXHAUSTED" in error_message:
            bot.reply_to(message, "К сожалению, достигнут лимит запросов Gemini API. Попробуйте позже.")
        else:
            bot.reply_to(message, f"Произошла ошибка при обработке запроса: {error_message}")


if __name__ == '__main__':
    print("Бот запущен...")
    bot.polling()
