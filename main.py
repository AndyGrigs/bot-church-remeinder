from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from dotenv import load_dotenv
import os
import json
from datetime import datetime

# Завантаження змінних із .env файлу
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

user_states = {}

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

# Список проповідників
PREACHERS =  [
    "Басько П.", "Біленко Ю.", "Мосійчук В.", "Мироненко І.",
    "Барановський М.", "Пономарьов А.", "Замуруєв В.", "Григоров А.",
    "Савостін В.", "Козак Є.", "Кулик Є.", "Ковальчук Ю.",
    "Савостін І.", "Суржа П.", "Кітченко Я.", "Волос В.",
    "Сардак Р."
]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Вітаю! Я церковний бот. Я буду нагадувати про проповідників в зібранні).")

async def reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Не забудьте, що цього тижня у нас відбудеться церковний захід!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда для показу списку команд"""
    commands = """
Доступні команди:
/start - Почати спілкування з ботом
/reminder - Нагадування про захід
/help - Показати список доступних команд
/add - Додати нову проповідь
/end - Показати таблицю проповідей
"""
    await update.message.reply_text(commands)

# Команда для додавання нової проповіді
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введіть дату проповіді, наприклад, 01.01.2025, у форматі DD.MM.YYYY:")
    user_states[update.effective_user.id] = "waiting_for_date"

# Обробка введення дати
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id in user_states:
        state = user_states[user_id]

        if state == "waiting_for_date":
            # Перевіряємо формат дати
            date = update.message.text
            try:
                # Перетворюємо введену дату у формат DD.MM.YYYY
                parsed_date = datetime.strptime(date, "%d.%m.%Y")
                formatted_date = parsed_date.strftime("%d.%m.%Y")

                # Зберігаємо дату і чекаємо вибору проповідника
                user_states[user_id] = {"state": "waiting_for_preacher", "date": formatted_date}

                # Відправляємо список проповідників
                keyboard = [[KeyboardButton(name)] for name in PREACHERS]
                reply_markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
                await update.message.reply_text("Оберіть проповідника:", reply_markup=reply_markup)

            except ValueError:
                await update.message.reply_text("Неправильний формат дати. Введіть у форматі (день.місяць.рік) DD.MM.YYYY:")

        elif state.get("state") == "waiting_for_preacher":
            # Зберігаємо вибір проповідника
            preacher = update.message.text
            date = state["date"]

            # Завантажуємо розклад
            schedule = load_schedule()

            # Додаємо новий запис
            schedule[date] = preacher
            save_schedule(schedule)

            # Підтвердження
            await update.message.reply_text(f"Проповідь на {date} збережено. Проповідник: {preacher}")
            
            # Очищення стану
            del user_states[user_id]

# Команда для показу таблиці
# async def end_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     schedule = load_schedule()

#     if not schedule:
#         await update.message.reply_text("Розклад порожній.")
#         return

#     # Формування таблиці в Markdown
#     table = "| Дата       | Проповідник     |\n"
#     table += "|------------|-----------------|\n"
#     for date, preacher in sorted(schedule.items()):
#         table += f"| {date} | {preacher} |\n"

#     # Надсилання таблиці
#     await update.message.reply_text(f"Ось розклад проповідей:\n\n```\n{table}\n```", parse_mode="Markdown")
# Команда для формування таблиці
# async def end_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     schedule = load_schedule()

#     if not schedule:
#         await update.message.reply_text("Розклад порожній.")
#         return

#     # Отримання унікальних дат і сортування
#     dates = sorted(set(schedule.keys()))

#     # Формування заголовка таблиці
#     header = "| Ім'я               | " + " | ".join(dates) + " |\n"
#     header += "|--------------------|" + "|".join(["----------"] * len(dates)) + "|\n"

#     # Формування рядків таблиці для кожного проповідника
#     rows = []
#     for preacher in PREACHERS:
#         row = [preacher]  # Починаємо рядок із імені
#         for date in dates:
#             # Перевіряємо, чи проповідник має запис на цю дату
#             if schedule.get(date) == preacher:
#                 row.append("🟡")
#             else:
#                 row.append(" ")
#         rows.append("| " + " | ".join(row) + " |")

#     # Формуємо фінальну таблицю
#     table = header + "\n".join(rows)

#     # Надсилання таблиці
#     await update.message.reply_text(f"Ось розклад проповідей:\n\n```\n{table}\n```", parse_mode="Markdown")
# Мапа днів тижня
# Мапа скорочень днів тижня
SHORT_DAYS_OF_WEEK = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Нд"]

# Фіксована ширина для стовпців
COLUMN_WIDTH = 5

# Команда для формування таблиці
async def end_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    schedule = load_schedule()

    if not schedule:
        await update.message.reply_text("Розклад порожній.")
        return

    # Отримання унікальних дат і сортування
    dates = sorted(set(schedule.keys()))

    # Формування заголовка таблиці
    header = f"| {'Ім\'я':<17} | " + " | ".join(f"{datetime.strptime(date, '%d.%m.%Y').strftime('%d.%m'):<{COLUMN_WIDTH}}" for date in dates) + " |\n"
    separator = "|-------------------|" + "|".join(["-" * COLUMN_WIDTH] * len(dates)) + "|\n"
    days_row = f"| {'День тижня':<17} | " + " | ".join(
        f"{SHORT_DAYS_OF_WEEK[datetime.strptime(date, '%d.%m.%Y').weekday()]:<{COLUMN_WIDTH}}" for date in dates
    ) + " |\n"

    # Формування рядків таблиці для кожного проповідника
    rows = []
    for preacher in PREACHERS:
        row = [f"{preacher:<17}"]  # Ім'я проповідника
        for date in dates:
            if schedule.get(date) == preacher:
                row.append("🟡".center(COLUMN_WIDTH))  # Жовтий круг без пробілів
            else:
                row.append(" ".center(COLUMN_WIDTH))  # Порожня комірка
        rows.append("| " + " | ".join(row) + " |")

    # Формуємо повну таблицю
    table = header + separator + days_row + separator + "\n".join(rows)

    # Надсилання таблиці
    await update.message.reply_text(f"```\n{table}\n```", parse_mode="Markdown")


def main():
    # Створення бота
    application = Application.builder().token(BOT_TOKEN).build()

    # Додавання команд до бота
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("reminder", reminder))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add", add_command))
    application.add_handler(CommandHandler("end", end_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
