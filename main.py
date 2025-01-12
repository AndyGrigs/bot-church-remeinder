import calendar
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, time
from pymongo import MongoClient
from bson.objectid import ObjectId


# Завантаження змінних із .env файлу
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
GROUP_CHAT_ID = os.getenv('GROUP_CHAT_ID')
MONGO_URI = os.getenv('MONGO_URI') 

if not BOT_TOKEN or not GROUP_CHAT_ID or not MONGO_URI:
    print("Помилка: BOT_TOKEN або GROUP_CHAT_ID не встановлено. Перевірте файл .env.")
    exit(1)

try:
    GROUP_CHAT_ID = int(GROUP_CHAT_ID)  # Перетворюємо на ціле число
except ValueError:
    print("Помилка: GROUP_CHAT_ID повинен бути цілим числом.")
    exit(1)

user_states = {}


# client = MongoClient(MONGO_URI, ssl=True, ssl_cert_reqs=ssl.CERT_NONE)
# client = MongoClient(MONGO_URI, ssl_cert_reqs=ssl.CERT_NONE)
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
db = client["church_schedule"]  # Назва бази даних
collection = db["schedules"]  # Колекція для розкладів

def load_schedule():
    """Завантаження розкладу з MongoDB."""
    try:
        documents = collection.find({})
        schedule = {}
        for doc in documents:
            date = doc["date"]
            preachers = doc["preachers"]
            schedule[date] = preachers
        return schedule
    except Exception as e:
        print(f"Помилка при завантаженні розкладу: {e}")
        return {}

def save_schedule(new_entry):
    """Додавання нового запису до MongoDB."""
    try:
        for date, preacher in new_entry.items():
            existing_entry = collection.find_one({"date": date})
            if existing_entry:
                # Додаємо нового проповідника, якщо його ще немає
                if preacher not in existing_entry["preachers"]:
                    collection.update_one(
                        {"date": date},
                        {"$push": {"preachers": preacher}}
                    )
            else:
                # Створюємо новий запис
                collection.insert_one({"date": date, "preachers": [preacher]})
    except Exception as e:
        print(f"Помилка при збереженні розкладу: {e}")


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



# async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     await update.message.reply_text("Введіть дату проповіді (DD.MM.YYYY):")
#     user_states[update.effective_user.id] = "waiting_for_date"

def get_thursday_sunday_dates(year: int, month: int):
    """
    Повертає список дат (у форматі DD.MM.YYYY) для четвергів і неділь 
    у вказаному році та місяці.
    """
    # Дізнаємося, скільки днів у місяці
    _, days_in_month = calendar.monthrange(year, month)

    # Створюємо список усіх дат місяця
    all_dates = [
        datetime(year, month, day)
        for day in range(1, days_in_month + 1)
    ]

    # Потрібні лише четвер (weekday() = 3) та неділя (weekday() = 6)
    # (Пн=0, Вт=1, Ср=2, Чт=3, Пт=4, Сб=5, Нд=6)
    selected_dates = [
        d.strftime("%d.%m.%Y")
        for d in all_dates
        if d.weekday() in (3, 6)  # четвер і неділя
    ]

    return selected_dates

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Визначаємо поточний рік і місяць
    now = datetime.now()
    current_year = now.year
    current_month = now.month

    # Дати четвергів і неділь для поточного місяця
    current_month_dates = get_thursday_sunday_dates(current_year, current_month)

    # Визначаємо наступний місяць
    if current_month == 12:
        next_year = current_year + 1
        next_month = 1
    else:
        next_year = current_year
        next_month = current_month + 1

    # Дати четвергів і неділь для наступного місяця
    next_month_dates = get_thursday_sunday_dates(next_year, next_month)

    # Об'єднуємо дати обох місяців (можна залишити окремо, але зручніше одним списком)
    all_dates = current_month_dates + next_month_dates

    if not all_dates:
        await update.message.reply_text(
            "Немає доступних четвергів чи неділь у поточному або наступному місяці."
        )
        return

    # Готуємо клавіатуру з датами
    keyboard = [[KeyboardButton(date_str)] for date_str in all_dates]

    # Записуємо стан користувача
    user_states[update.effective_user.id] = "waiting_for_date"

    # Виводимо повідомлення з вибором дати
    await update.message.reply_text(
        "Оберіть дату проповіді (лише четвер або неділя):",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            one_time_keyboard=True,
            resize_keyboard=True
        ),
    )


# async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     user_id = update.effective_user.id

#     if user_id in user_states:
#         state = user_states[user_id]

#         if state == "waiting_for_date":
#             date = update.message.text
#             try:
#                 parsed_date = datetime.strptime(date, "%d.%m.%Y")
#                 formatted_date = parsed_date.strftime("%d.%m.%Y")

#                 user_states[user_id] = {"state": "waiting_for_preacher", "date": formatted_date}
#                 keyboard = [[KeyboardButton(name)] for name in PREACHERS]
#                 reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
#                 await update.message.reply_text("Оберіть проповідника:", reply_markup=reply_markup)
#             except ValueError:
#                 await update.message.reply_text("Неправильний формат дати. Введіть дату у форматі DD.MM.YYYY:")

#         elif state.get("state") == "waiting_for_preacher":
#             preacher = update.message.text
#             date = state["date"]

#             new_entry = {date: preacher}
#             save_schedule(new_entry)

#             schedule = load_schedule()
#             propov_idniki = ", ".join(schedule[date])
#             await update.message.reply_text(f"Проповідь на {date} збережено. Проповідники: {propov_idniki}")

            
#             del user_states[user_id]
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Перевіряємо, чи є користувач у user_states
    if user_id in user_states:
        state = user_states[user_id]

        # ---------------------------------------------------------------------
        # Якщо користувач щойно обрав дату
        # ---------------------------------------------------------------------
        if state == "waiting_for_date":
            # Записуємо обрану дату
            selected_date = update.message.text.strip()

            # Тепер ми чекаємо вибір проповідника
            user_states[user_id] = {
                "state": "waiting_for_preacher",
                "date": selected_date
            }

            # Формуємо клавіатуру з прізвищами проповідників
            keyboard = [[KeyboardButton(name)] for name in PREACHERS]

            await update.message.reply_text(
                "Оберіть проповідника:",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard,
                    one_time_keyboard=True,
                    resize_keyboard=True
                ),
            )

        # ---------------------------------------------------------------------
        # Якщо користувач обрав проповідника
        # ---------------------------------------------------------------------
        elif isinstance(state, dict) and state.get("state") == "waiting_for_preacher":
            preacher = update.message.text.strip()
            date = state["date"]

            # Зберігаємо запис у базі
            new_entry = {date: preacher}
            save_schedule(new_entry)

            schedule = load_schedule()
            propovidnyky = ", ".join(schedule[date])
            await update.message.reply_text(
                f"Проповідь на {date} збережено. Проповідники: {propovidnyky}"
            )

            # Очищаємо стан користувача
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




async def remind(context: ContextTypes.DEFAULT_TYPE):
    try:
        schedule = load_schedule()
        current_date = datetime.now().date()

        for date, preachers in schedule.items():
            schedule_date = datetime.strptime(date, "%d.%m.%Y")
            difference = (schedule_date - current_date).days

            if difference == 2:
                preachers_list = ", ".join(preachers)
                message = (
                    f"Нагадування!\n\n"
                    f"На зібранні{date}:\n"
                    f"Проповідують:{preachers_list}"
                )
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
    
    application.job_queue.run_daily(remind, time=datetime.time(9, 0), days=(2, 5))
    # application.job_queue.run_daily(remind, time=time(datetime.now().hour, datetime.now().minute + 1), days=(datetime.now().weekday(),))
    # application.job_queue.run_daily(remind, time=time(9, 0), days=(2, 5))
    # application.job_queue.run_repeating(remind, interval=10, name='remind_job')
    # application.job_queue.run_daily(remind, time=datetime.time(9, 0), days=(2, 5))
    # application.job_queue.run_daily(remind, time=datetime.time(9, 0), days=(2, 5))
    # application.job_queue.run_repeating(remind, interval=3600, name='remind_job')
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

  
    application.run_polling()

if __name__ == "__main__":
    main()
