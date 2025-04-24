import os
import logging
import random
import pandas as pd
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# 🔹 API Token from BotFather
TOKEN = os.getenv('TELEGRAM_BOT_API_KEY')

# 🔹 Load Excel files
df = pd.read_excel("/app/questions.xlsx", engine="openpyxl")  # Санкт-Петербург
df_yaroslavl = pd.read_excel("/app/questions_Yaroslavl.xlsx", engine="openpyxl")  # Ярославль

# 🔹 Fill missing values
df = df.fillna("-")
df_yaroslavl = df_yaroslavl.fillna("-")

# 🔹 Convert to list of dicts
all_questions = df.to_dict(orient="records")
all_yaroslavl = df_yaroslavl.to_dict(orient="records")

# 🔹 Logging config
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.WARNING
)

user_data = {}

async def start(update: Update, context: CallbackContext) -> None:
    """Start command: prompts city selection"""
    user_id = update.message.chat_id
    keyboard = [["Санкт-Петербург"], ["Ярославль"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Привет! Выбери город, чтобы начать тест:", reply_markup=reply_markup)

async def quiz(update: Update, context: CallbackContext) -> None:
    """Sends a question"""
    user_id = update.message.chat_id

    if user_id not in user_data or "questions" not in user_data[user_id]:
        await update.message.reply_text("Сначала выбери город командой /start.")
        return

    user_info = user_data[user_id]

    if user_info["current_question"] >= len(user_info["questions"]):
        score = user_info["score"]
        keyboard = [["🔄 Пройти заново"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text(
            f"✅ Тест завершён! Ты набрал {score} из 25 баллов.\n\nХотите попробовать снова?",
            reply_markup=reply_markup
        )
        return

    question_index = user_info["current_question"]
    question = user_info["questions"][question_index]
    user_info["current_question"] += 1

    context.user_data["current_question"] = question

    options = [(k, str(v)) for k, v in question.items() if k.startswith("Вариант") and str(v).strip() != "-"]
    random.shuffle(options)

    context.user_data["shuffled_options"] = [val.lower().strip() for _, val in options]

    keyboard = [[val] for _, val in options]
    keyboard.append(["🏁 Завершить тест"])  # Add end test button

    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(question["Вопрос"], reply_markup=reply_markup)

async def answer(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    text = update.message.text.strip()

    if text == "🔄 Пройти заново":
        user_data.pop(user_id, None)
        context.user_data.clear()
        await start(update, context)
        return

    if text == "▶️ Начать тест":
        await quiz(update, context)
        return

    if text == "🏁 Завершить тест":
        score = user_data[user_id]["score"]
        keyboard = [["🔄 Пройти заново"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text(
            f"🏁 Тест завершён досрочно! Твой результат: {score} из 25.",
            reply_markup=reply_markup
        )

        context.user_data.clear()
        return

    if user_id not in user_data:
        if text in ["Санкт-Петербург", "Ярославль"]:
            selected_questions = all_questions if text == "Санкт-Петербург" else all_yaroslavl
            selected_questions = [
                q for q in selected_questions
                if any(str(q.get(k)).strip() != "-" for k in q if k.startswith("Вариант"))
            ]
            if not selected_questions:
                await update.message.reply_text("⚠️ Вопросы не найдены.")
                return

            context.user_data.clear()
            user_data[user_id] = {
                "city": text,
                "score": 0,
                "current_question": 0,
                "questions": random.sample(selected_questions, min(len(selected_questions), 25))
            }

            keyboard = [["▶️ Начать тест"]]
            reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

            await update.message.reply_text(
                f"✅ Город {text} выбран. Нажми кнопку ниже, чтобы начать тест.",
                reply_markup=reply_markup
            )
            return
        else:
            await update.message.reply_text("Пожалуйста, выбери город из предложенных.")
            return

    if "current_question" not in context.user_data or "shuffled_options" not in context.user_data:
        await update.message.reply_text("Напиши /start и выбери город, чтобы начать тест.")
        return

    question = context.user_data["current_question"]
    correct_answer = str(question["Правильный ответ (текст)"]).strip().lower()
    user_answer = text.strip().lower()

    if user_answer == correct_answer:
        user_data[user_id]["score"] += 1
        await update.message.reply_text("✅ Верно!")
    else:
        await update.message.reply_text(f"❌ Неверно. Правильный ответ: {question['Правильный ответ (текст)']}")

    await quiz(update, context)

async def stats(update: Update, context: CallbackContext) -> None:
    user_id = update.message.chat_id
    if user_id in user_data:
        score = user_data[user_id]["score"]
        await update.message.reply_text(f"📊 Твой текущий результат: {score} из 25.")
    else:
        await update.message.reply_text("Ты ещё не начал тест. Напиши /start!")

def main():
    print("🔹 Бот запускается...")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer))

    print("✅ Бот работает! Ожидание сообщений...")
    app.run_polling()

if __name__ == "__main__":
    main()
