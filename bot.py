import telebot
from telebot import types
import os
from dotenv import load_dotenv

# Загрузка переменных из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

BORYA_CHAT_ID = int(os.getenv("BORYA_CHAT_ID"))
PICKUP_ADDRESS = os.getenv("PICKUP_ADDRESS")
CARD_NUMBER = os.getenv("CARD_NUMBER")

# Хранилище данных пользователей
user_data = {}

# Команда /start
@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🍌 Заказать")
    markup.row("😂 Анекдот", "👨‍💻 Создатель")
    bot.send_message(message.chat.id, "Привет! Я бот Бананчеллы! Что хочешь сделать?", reply_markup=markup)

# Кнопка: Заказать
@bot.message_handler(func=lambda message: message.text == "🍌 Заказать")
def begin_order(message):
    user_data[message.chat.id] = {'quantity': 1}
    with open("static/banan.png", 'rb') as photo:
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("➖", callback_data="decrease"),
            types.InlineKeyboardButton("1 шт. — 999₽", callback_data="none"),
            types.InlineKeyboardButton("➕", callback_data="increase")
        )
        bot.send_photo(
            message.chat.id,
            photo,
            caption="🍌 ХОЧУ БАНАНЧЕЛЛИТЬ!\n\nВыбери количество:",
            reply_markup=markup
        )

# Кнопка: Анекдот
@bot.message_handler(func=lambda message: message.text == "😂 Анекдот")
def send_joke(message):
    bot.send_message(
        message.chat.id,
        "😂 Почему банан пошёл к доктору?\nПотому что он не мог найти свою кожуру! 🍌"
    )

# Кнопка: Создатель
@bot.message_handler(func=lambda message: message.text == "👨‍💻 Создатель")
def creator_info(message):
    bot.send_message(
        message.chat.id,
        "Меня создал начинающий IT гений, гуру гастрономии @PuraVidaMan"
    )

# Обработка inline-кнопок
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    chat_id = call.message.chat.id
    data = call.data
    if chat_id not in user_data:
        user_data[chat_id] = {'quantity': 1}
    quantity = user_data[chat_id]['quantity']

    if data == "increase" and quantity < 100:
        quantity += 1
    elif data == "decrease" and quantity > 1:
        quantity -= 1
    elif data == "pay":
        price = quantity * 999
        msg = (
            f"✅ Заказ принят!\n\n"
            f"📦 {quantity} шт. × 999 ₽ = {price}₽\n"
            f"💳 Переведи на карту: {CARD_NUMBER} (Яндекс Банк)\n"
            f"📍 Самовывоз: {PICKUP_ADDRESS}\n\n"
            f"После оплаты нажми кнопку 'Я оплатил'"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("✅ Я оплатил", callback_data="paid"))
        bot.edit_message_caption(chat_id=chat_id, message_id=call.message.message_id, caption=msg, reply_markup=markup)
        user_data[chat_id]['quantity'] = quantity
        return
    elif data == "paid":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn = types.KeyboardButton("📱 Поделиться номером", request_contact=True)
        markup.add(btn)
        bot.send_message(chat_id, "Пожалуйста, отправь свой номер телефона для подтверждения оплаты", reply_markup=markup)
        return

    # Обновляем интерфейс
    user_data[chat_id]['quantity'] = quantity
    price = quantity * 999
    markup = types.InlineKeyboardMarkup()
    markup.row(
        types.InlineKeyboardButton("➖", callback_data="decrease"),
        types.InlineKeyboardButton(f"{quantity} шт. — {price}₽", callback_data="none"),
        types.InlineKeyboardButton("➕", callback_data="increase")
    )
    markup.add(types.InlineKeyboardButton("✅ Оплатить", callback_data="pay"))

    try:
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=markup)
    except Exception as e:
        print("Ошибка обновления кнопок:", e)

# Получение номера телефона и уведомление Боре
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    if not message.contact:
        bot.send_message(message.chat.id, "❌ Вы не отправили номер. Попробуйте ещё раз.")
        start(message)
        return

    phone = message.contact.phone_number
    username = f"@{message.from_user.username}" if message.from_user.username else "Без username"
    quantity = user_data.get(message.chat.id, {}).get('quantity', '?')

    notif = (
        f"🍌 Новый заказ!\n"
        f"👤 Клиент: {username}\n"
        f"📞 Телефон: {phone}\n"
        f"📦 Кол-во: {quantity} шт.\n"
        f"📍 Самовывоз: {PICKUP_ADDRESS}"
    )

    try:
        bot.send_message(BORYA_CHAT_ID, notif)
        bot.send_message(message.chat.id, "✅ Уведомление отправлено организатору!")
        print(f"📤 Отправлено Боре: {notif}")
    except Exception as e:
        print("Ошибка при отправке сообщения Боре:", e)
        bot.send_message(message.chat.id, "❌ Не удалось отправить уведомление организатору.")

    # Возврат в стартовое меню
    start(message)

# Запуск бота
if __name__ == "__main__":
    print("🚀 Бот Бананчеллы запущен!")
    bot.polling(none_stop=True)
