import telebot
import time

TOKEN = "8961168833:AAHX1WQPNPFyaeHjmBY3HY2imTT5ifOGKeE"  # СЮДА ВСТАВЬ ТОКЕН ОТ @BotFather
bot = telebot.TeleBot(TOKEN)

# База питомцев (пока в памяти, потом можно улучшить)
pets = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привет! Я бот с питомцами 🐾\nКоманды: /newpet, /feed, /play, /status, /dress")

@bot.message_handler(commands=['newpet'])
def new_pet(message):
    user_id = message.from_user.id
    if user_id in pets:
        bot.send_message(message.chat.id, "У тебя уже есть питомец!")
        return
    pets[user_id] = {"голод": 50, "счастье": 50, "дни": 0, "одежда": "без одежды"}
    bot.send_message(message.chat.id, "Ты завёл питомца! 🎉 Теперь корми (/feed), играй (/play) и смотри статус (/status).")

@bot.message_handler(commands=['feed'])
def feed(message):
    user_id = message.from_user.id
    if user_id not in pets:
        bot.send_message(message.chat.id, "Сначала заведи питомца командой /newpet")
        return
    pets[user_id]["голод"] = min(100, pets[user_id]["голод"] + 20)
    bot.send_message(message.chat.id, "Питомец покормлен! 🍖 Голод +20")

@bot.message_handler(commands=['play'])
def play(message):
    user_id = message.from_user.id
    if user_id not in pets:
        bot.send_message(message.chat.id, "Сначала заведи питомца командой /newpet")
        return
    pets[user_id]["счастье"] = min(100, pets[user_id]["счастье"] + 15)
    bot.send_message(message.chat.id, "Питомец поиграл! 🎾 Счастье +15")

@bot.message_handler(commands=['status'])
def status(message):
    user_id = message.from_user.id
    if user_id not in pets:
        bot.send_message(message.chat.id, "Нет питомца. Заведи через /newpet")
        return
    data = pets[user_id]
    text = f"📊 Статус питомца:\n🍖 Голод: {data['голод']}\n😊 Счастье: {data['счастье']}\n📅 Дней: {data['дни']}\n👕 Одежда: {data['одежда']}"
    bot.send_message(message.chat.id, text)

@bot.message_handler(commands=['dress'])
def dress(message):
    user_id = message.from_user.id
    if user_id not in pets:
        bot.send_message(message.chat.id, "Сначала заведи питомца /newpet")
        return
    options = ["без одежды", "шапка 🧢", "шарф 🧣", "очки 🕶️"]
    current = pets[user_id]["одежда"]
    idx = options.index(current) if current in options else 0
    new_idx = (idx + 1) % len(options)
    pets[user_id]["одежда"] = options[new_idx]
    bot.send_message(message.chat.id, f"Теперь на питомце: {options[new_idx]}")

def update_days():
    while True:
        time.sleep(86400)
        for user_id in pets:
            pets[user_id]["дни"] += 1

import threading
thread = threading.Thread(target=update_days)
thread.daemon = True
thread.start()

print("✅ Бот запущен и работает круглосуточно!")
bot.polling()
