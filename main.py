import logging
import openai
import os
from aiogram import Bot, Dispatcher, executor, types
from dotenv import load_dotenv
import urllib.parse

# Завантаження змінних середовища
load_dotenv()

# Налаштування
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher(bot)
openai.api_key = OPENAI_API_KEY

user_data = {}

questions = [
    "Який стиль готелів тобі ближче?",
    "Яка цінова категорія тобі підходить?",
    "Наскільки важлива велика кількість готелів?",
    "✍️ Напиши кілька слів про свої вподобання: що тобі важливо в готелі, сервісі або відпочинку.",
    "🏙️ В яке місто ви плануєте подорож?"
]

style_kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add("Cozy", "Modern", "Classic")
price_kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add("Economy", "Midscale", "Upscale", "Upper Upscale", "Luxury")
quantity_kb = types.ReplyKeyboardMarkup(resize_keyboard=True).add("High", "Medium", "Low")

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    user_data[message.from_user.id] = {}
    await message.answer("👋 Привіт! Давай підберемо програму лояльності.")
    await message.answer(f"Питання 1/5: {questions[0]}", reply_markup=style_kb)

@dp.message_handler(lambda m: m.text in ["Cozy", "Modern", "Classic"])
async def handle_style(message: types.Message):
    user_data[message.from_user.id]["style"] = message.text
    await message.answer(f"Питання 2/5: {questions[1]}", reply_markup=price_kb)

@dp.message_handler(lambda m: m.text in ["Economy", "Midscale", "Upscale", "Upper Upscale", "Luxury"])
async def handle_price(message: types.Message):
    user_data[message.from_user.id]["price"] = message.text
    await message.answer(f"Питання 3/5: {questions[2]}", reply_markup=quantity_kb)

@dp.message_handler(lambda m: m.text in ["High", "Medium", "Low"])
async def handle_quantity(message: types.Message):
    user_data[message.from_user.id]["quantity"] = message.text
    await message.answer(f"Питання 4/5: {questions[3]}", reply_markup=types.ReplyKeyboardRemove())

@dp.message_handler(lambda m: "preferences" not in user_data.get(m.from_user.id, {}))
async def handle_preferences(message: types.Message):
    user_data[message.from_user.id]["preferences"] = message.text
    await message.answer(f"Питання 5/5: {questions[4]}")

@dp.message_handler(lambda m: "destination" not in user_data.get(m.from_user.id, {}))
async def handle_destination(message: types.Message):
    user_data[message.from_user.id]["destination"] = message.text
    data = user_data[message.from_user.id]

    prompt = f"""
Користувач шукає готель з наступними характеристиками:
- Стиль готелю: {data['style']}
- Цінова категорія: {data['price']}
- Кількість готелів у мережі важлива: {data['quantity']}
- Вподобання: {data['preferences']}
- Місто або країна: {data['destination']}

Порекомендуй:
1. Назву бренду та програму лояльності, яка найкраще підходить.
2. Коротко вкажи переваги програми.
3. Приклад готелю в цьому місті (назва).
4. Точну назву готелю окремо.
6. Якщо можливо, додай цікаву або романтичну деталь, пов'язану з готелем або місцем.
"""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=800
    )

    reply = response.choices[0].message.content

    hotel_lines = [line for line in reply.split('\n') if line.strip().startswith("4.")]
    hotel_name = hotel_lines[0][2:].strip() if hotel_lines else data["destination"]
    query = urllib.parse.quote(f"{hotel_name}, {data['destination']}")
    google_maps_url = f"https://www.google.com/maps/search/?api=1&query={query}"

    await message.answer(f"📌 Ось що я рекомендую:\n{reply}\n\n📍 Переглянь на Google Maps: {google_maps_url}")

if __name__ == '__main__':
    print("🤖 Бот запущено.")
    executor.start_polling(dp)
