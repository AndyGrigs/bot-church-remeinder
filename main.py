from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
import os
import json

# Завантаження змінних із .env файлу
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')



def load_schedule():
    try:
        with open("schedule.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Збереження розкладу у файл
def save_schedule(schedule):
    with open("schedule.json", "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=4)



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Вітаю! Я церковний бот. Я буду нагадувати про наші заходи.")

async def reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Не забудьте, що цього тижня у нас відбудеться церковний захід!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для показу списку команд"""
    commands = """
Доступні команди:
/start - Почати спілкування з ботом
/reminder - Нагадування про захід
/help - Показати список доступних команд
"""
    await update.message.reply_text(commands)


def main():
    # Створення бота
    application = Application.builder().token(BOT_TOKEN).build()

    # Додавання команд до бота
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reminder", reminder))
    application.add_handler(CommandHandler("help", help_command))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
