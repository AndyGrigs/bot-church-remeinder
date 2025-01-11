from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
import os
import json
from datetime import datetime, timedelta, time

# Завантаження змінних із .env файлу
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')

if not BOT_TOKEN or not GROUP_CHAT_ID:
    print("Помилка: BOT_TOKEN або GROUP_CHAT_ID не встановлено. Перевірте файл .env.")
    exit(1)

try:
    GROUP_CHAT_ID = int(GROUP_CHAT_ID)  # Перетворюємо на ціле число
except ValueError:
    print("Помилка: GROUP_CHAT_ID повинен бути цілим числом.")
    exit(1)

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
    await context.bot.send_message(chat_id=GROUP_CHAT_ID, text="Привіт! Я готовий працювати в групі.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands = """
Доступні команди:
/start - Почати спілкування з ботом
/add - Додати нову проповідь
/end - Показати розклад проповідей
"""
    await update.message.reply_text(commands)



async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введіть дату проповіді (DD.MM.YYYY):")
    user_states[update.effective_user.id] = "waiting_for_date"

def save_schedule(new_entry):
    """
    Додає новий запис до JSON-файлу, підтримуючи кілька проповідників на одну дату.
    """
    schedule = load_schedule()
    for date, preacher in new_entry.items():
        if date in schedule:
            if isinstance(schedule[date], list):
                if preacher not in schedule[date]:
                    schedule[date].append(preacher)
            else:
                if schedule[date] != preacher:
                    schedule[date] = [schedule[date], preacher]
        else:
            schedule[date] = [preacher]

    with open("schedule.json", "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=4)



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
            save_schedule(new_entry)

            schedule = load_schedule()
            propov_idniki = ", ".join(schedule[date])
            await update.message.reply_text(f"Проповідь на {date} збережено. Проповідники: {propov_idniki}")

            
            del user_states[user_id]

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

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"Помилка: {context.error}")


async def test_reminder(context: ContextTypes.DEFAULT_TYPE):
    try:
        print("Викликається test_reminder")
        await context.bot.send_message(chat_id=GROUP_CHAT_ID, text="Тестове нагадування працює!", parse_mode="Markdown")
        print("Тестове нагадування успішно відправлено!")
    except Exception as e:
        print(f"Помилка у test_reminder: {e}")

# async def repeat_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     """
#     Repeat a message in a Telegram chat.

#     Args:
#         update (telegram.Update): Telegram update object
#         context (telegram.ext.CallbackContext): Telegram context object
#     """
#     try:
#         message = update.message.text
#         chat_id = update.message.chat.id
#         await context.bot.send_message(chat_id=chat_id, text=message)
#     except Exception as e:
#         print(f"Error repeating message: {e}")

# async def remind(context: ContextTypes.DEFAULT_TYPE):
#     schedule = load_schedule()
#     current_time = datetime.now()
#     for date, preachers in schedule.items():
#         assigned_date = datetime.strptime(date, "%d.%m.%Y")
#         reminder_time = assigned_date - timedelta(hours=36)
#         if current_time >= reminder_time:
#             message = f"🔔 Нагадування! Наступні проповідують: {', '.join(preachers)}"
#             await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=message)
#     return

# async def remind(context: ContextTypes.DEFAULT_TYPE):
#     schedule = load_schedule()
#     current_time = datetime.now()
#     current_day = current_time.weekday()
#     current_hour = current_time.hour
#     if (current_day == 2 and current_hour == 9) or (current_day == 5 and current_hour == 9):
#         if current_day == 2:
#             tomorrow = current_time.date() + timedelta(days=1)
#             tomorrow_str = tomorrow.strftime("%d.%m.%Y")
#             if tomorrow_str in schedule:
#                 message = f"Завтра проповідує: {', '.join(schedule[tomorrow_str])}"
#                 await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=message)
#         elif current_day == 5:
#             sunday = current_time.date() + timedelta(days=2)
#             sunday_str = sunday.strftime("%d.%m.%Y")
#             if sunday_str in schedule:
#                 message = f"Неділя проповідує: {', '.join(schedule[sunday_str])}"
#                 await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=message)
#     return

async def remind(context: ContextTypes.DEFAULT_TYPE):
    print()
    try:
        schedule = load_schedule()
        current_time = datetime.now()

        # Середа - нагадування на четвер
        if current_time.weekday() == 2:  # Середа
            tomorrow = current_time.date() + timedelta(days=1)
            tomorrow_str = tomorrow.strftime("%d.%m.%Y")
            if tomorrow_str in schedule:
                message = f"🔔 Нагадування! Завтра проповідують: {', '.join(schedule[tomorrow_str])}."
                await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=message)

        # Субота - нагадування на неділю
        elif current_time.weekday() == 5:  # Субота
            sunday = current_time.date() + timedelta(days=2)
            sunday_str = sunday.strftime("%d.%m.%Y")
            if sunday_str in schedule:
                message = f"🔔 Нагадування! У неділю проповідують: {', '.join(schedule[sunday_str])}."
                await context.bot.send_message(chat_id=GROUP_CHAT_ID, text=message)

    except Exception as e:
        print(f"Помилка у функції remind: {e}")


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add", add_command))
    application.add_handler(CommandHandler("end", end_command))
    application.add_handler(CommandHandler("get_chat_id", get_chat_id))
    application.add_error_handler(error_handler)
    
    # application.job_queue.run_daily(remind, time=time(datetime.now().hour, datetime.now().minute + 1), days=(datetime.now().weekday(),))
    # application.job_queue.run_daily(remind, time=time(9, 0), days=(2, 5))
    application.job_queue.run_repeating(remind, interval=10, name='remind_job')
    # application.job_queue.run_daily(remind, time=datetime.time(9, 0), days=(2, 5))
    # application.job_queue.run_daily(remind, time=datetime.time(9, 0), days=(2, 5))
    # application.job_queue.run_repeating(remind, interval=3600, name='remind_job')
    # application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, repeat_message))
  
    application.run_polling()

if __name__ == "__main__":
    main()
