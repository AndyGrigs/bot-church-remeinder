from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta

# Завантаження змінних із .env файлу
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')

user_states = {}

def load_schedule():
    """
    Завантаження існуючого розкладу з JSON-файлу.
    """
    try:
        with open("schedule.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


# Список проповідників
PREACHERS = [
    "Басько П.", "Біленко Ю.", "Мосійчук В.", "Мироненко І.",
    "Барановський М.", "Пономарьов А.", "Замуруєв В.", "Григоров А.",
    "Савостін В.", "Козак Є.", "Кулик Є.", "Ковальчук Ю.",
    "Савостін І.", "Суржа П.", "Кітченко Я.", "Волос В.",
    "Сардак Р."
]

# Мапа скорочень днів тижня
SHORT_DAYS_OF_WEEK = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Вітаю! Я церковний бот. Я буду нагадувати про проповідників в зібранні).")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands = """
Доступні команди:
/start - Почати спілкування з ботом
/add - Додати нову проповідь
/end - Показати розклад проповідей
/get_chat_id - Дізнатися Chat ID групи
"""
    await update.message.reply_text(commands)

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введіть дату проповіді (DD.MM.YYYY):")
    user_states[update.effective_user.id] = "waiting_for_date"


def save_schedule(new_entry):
    """
    Додає новий запис до JSON-файлу, підтримуючи кілька проповідників на одну дату.
    """
    schedule = load_schedule()  # Завантажуємо існуючі дані

    for date, preacher in new_entry.items():
        if date in schedule:
            # Якщо дата вже існує, додаємо нового проповідника до списку
            if isinstance(schedule[date], list):
                if preacher not in schedule[date]:  # Уникаємо дублювання
                    schedule[date].append(preacher)
            else:
                # Якщо для дати записано одного проповідника, перетворюємо на список
                if schedule[date] != preacher:
                    schedule[date] = [schedule[date], preacher]
        else:
            # Якщо дати немає, додаємо її
            schedule[date] = [preacher]

    # Зберігаємо оновлені дані
    with open("schedule.json", "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=4)

# Оновлена функція обробки вибору проповідника
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in user_states:
        state = user_states[user_id]

        if state == "waiting_for_date":
            date = update.message.text
            try:
                parsed_date = datetime.strptime(date, "%d.%m.%Y")
                formatted_date = parsed_date.strftime("%d.%m.%Y")

                user_states[user_id] = {"state": "waiting_for_preacher", "date": formatted_date}
                keyboard = [[KeyboardButton(name)] for name in PREACHERS]
                reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
                await update.message.reply_text("Оберіть проповідника:", reply_markup=reply_markup)

            except ValueError:
                await update.message.reply_text("Неправильний формат дати. Введіть дату у форматі DD.MM.YYYY:")

        elif state.get("state") == "waiting_for_preacher":
            preacher = update.message.text
            date = state["date"]

            new_entry = {date: preacher}
            save_schedule(new_entry)  # Додаємо або оновлюємо запис у файл

            # Завантажуємо оновлений розклад, щоб відобразити список проповідників для цієї дати
            schedule = load_schedule()
            propov_idniki = ", ".join(schedule[date])
            await update.message.reply_text(f"Проповідь на {date} збережено. Проповідники: {propov_idniki}")

            # Додаємо завдання для нагадування (тільки для першого проповідника, якщо потрібно)
            event_time = datetime.strptime(date, "%d.%m.%Y")
            reminder_time = datetime.now() + timedelta(minutes=5)

            if reminder_time > datetime.now():
                context.job_queue.run_once(
                    reminder_job,
                    when=reminder_time,
                    data={"chat_id": GROUP_CHAT_ID, "date": date, "preacher": preacher},
                    name=f"reminder_{date}_{preacher}"
                )
                await update.message.reply_text(f"Тестове нагадування для {preacher} буде через 5 хвилин.")

            del user_states[user_id]


async def reminder_job(context: ContextTypes.DEFAULT_TYPE):
    job_data = context.job.data
    chat_id = job_data["chat_id"]
    date = job_data["date"]
    preacher = job_data["preacher"]

    text = f"🔔 Нагадування!\n\nПроповідник: *{preacher}*.\nДата: {date}."
    await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")

async def end_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    schedule = load_schedule()

    if not schedule:
        await update.message.reply_text("Розклад порожній.")
        return

    result = "*Розклад проповідей:*\n\n"
    for date, preacher in sorted(schedule.items()):
        day_of_week = SHORT_DAYS_OF_WEEK[datetime.strptime(date, "%d.%m.%Y").weekday()]
        result += f"- {date} ({day_of_week}): {preacher}\n"

    await update.message.reply_text(result, parse_mode="Markdown")

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"Chat ID цієї групи: {chat_id}")

def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add", add_command))
    application.add_handler(CommandHandler("end", end_command))
    application.add_handler(CommandHandler("get_chat_id", get_chat_id))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()
