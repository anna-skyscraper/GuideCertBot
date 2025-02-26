import logging
import random
import pandas as pd
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# 🔹 Вставь свой API-токен от @BotFather
TOKEN = "8165670569:AAFMJr0woZA4RSZApyhrAQgFzfe2F1XY_wc"

# 🔹 Загружаем Excel
file_path = "questions.xlsx"
df = pd.read_excel(file_path, engine="openpyxl")

# 🔹 Заполняем пустые значения, чтобы избежать NaN
df = df.fillna("-")

# 🔹 Выводим заголовки в консоль для проверки
print("Заголовки столбцов в файле:", df.columns.tolist())

# 🔹 Преобразуем в список словарей
all_questions = df.to_dict(orient="records")

# 🔹 Настраиваем логирование (чтобы не было лишних сообщений)
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.WARNING  # Показываем только важные ошибки
)

# 🔹 Словарь для хранения данных пользователей
user_data = {}

async def start(update: Update, context: CallbackContext) -> None:
    """Запуск бота"""
    user_id = update.message.chat_id
    user_data[user_id] = {"score": 0, "current_question": 0, "questions": random.sample(all_questions, 35)}
    await update.message.reply_text("Привет! Давай проверим твои знания. Напиши /quiz, чтобы начать тест.")

async def quiz(update: Update, context: CallbackContext) -> None:
    """Выдаёт вопрос пользователю"""
    user_id = update.message.chat_id

    if user_id not in user_data:
        await update.message.reply_text("Напиши /start, чтобы начать тест.")
        return

    user_info = user_data[user_id]
    
    if user_info["current_question"] >= len(user_info["questions"]):
        # 🔹 Тест завершён – показываем кнопку "Пройти заново"
        score = user_info["score"]
        keyboard = [["🔄 Пройти заново"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

        await update.message.reply_text(f"✅ Тест завершён! Ты набрал {score} из 35 баллов.\n\nХотите попробовать снова?", reply_markup=reply_markup)
        return

    question = user_info["questions"][user_info["current_question"]]
    user_info["current_question"] += 1  # Переход к следующему вопросу
    context.user_data["current_question"] = question  # Сохраняем текущий вопрос

    # 🔹 Преобразуем все варианты ответа в строки
    options = [str(question["Вариант 1"]), str(question["Вариант 2"]), str(question["Вариант 3"])]

    # 🔹 Создаём клавиатуру (делаем кнопки вертикально)
    keyboard = [[options[0]], [options[1]], [options[2]]]
    reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(question["Вопрос"], reply_markup=reply_markup)

async def answer(update: Update, context: CallbackContext) -> None:
    """Проверяет ответ пользователя"""
    user_id = update.message.chat_id
    text = update.message.text.strip().lower()  # 🔹 Удаляем пробелы и приводим к нижнему регистру

    if text == "🔄 пройти заново":
        await start(update, context)  # Перезапускаем тест
        return

    if "current_question" not in context.user_data:
        await update.message.reply_text("Напиши /quiz, чтобы начать тест.")
        return

    question = context.user_data["current_question"]
    correct_answer = str(question["Правильный ответ (текст)"]).strip().lower()  # 🔹 Аналогично очищаем правильный ответ

    if text == correct_answer:
        user_data[user_id]["score"] += 1
        await update.message.reply_text("✅ Верно!")
    else:
        await update.message.reply_text(f"❌ Неверно. Правильный ответ: {question['Правильный ответ (текст)']}")

    # Показываем следующий вопрос
    await quiz(update, context)

async def stats(update: Update, context: CallbackContext) -> None:
    """Показывает текущий результат пользователя"""
    user_id = update.message.chat_id
    if user_id in user_data:
        score = user_data[user_id]["score"]
        await update.message.reply_text(f"📊 Твой текущий результат: {score} из 35.")
    else:
        await update.message.reply_text("Ты ещё не начал тест. Напиши /quiz!")

def main():
    """Запуск бота"""
    print("🔹 Бот запускается...")

    # 🔹 Новый способ работы с bot API в версии 20+
    app = Application.builder().token(TOKEN).build()

    # Добавляем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("quiz", quiz))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, answer))

    print("✅ Бот работает! Ожидание сообщений...")

    # Запускаем бота
    app.run_polling()

if __name__ == "__main__":
    main()
