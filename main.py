from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv
import os

# Завантаження змінних із .env файлу
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')


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
