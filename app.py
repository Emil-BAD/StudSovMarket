from dotenv import load_dotenv
import os
import logging
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler,  CallbackContext, PollHandler, PollAnswerHandler, MessageHandler, filters, CallbackQueryHandler

load_dotenv()
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = [833046485]
poll_results = {}
completed_users = set()

bot = Bot(token=TOKEN)

start_message = (
    f"Добро пожаловать в &quot;<b>СС Маркет</b>&quot; – официальный бот от Студенческого совета "
    f"общежития №1 🎉\n\n"
    f"Здесь вы можете легко и быстро заказать свои любимые энергетические напитки, "
    f"не выходя из общежития. 💪\n\n"
    f"✨ <b>Что вы найдете в боте?</b>\n"
    f"- Удобный каталог с ассортиментом энергетиков.\n"
    f"- Актуальные цены и наличие.\n"
    f"- Быстрое оформление заказа.\n"
    f"- Поддержка и ответы на ваши вопросы.\n\n"
    f"🛒 <b>Как заказать?</b>\n"
    f"1. Выберите напиток из меню.\n"
    f"2. Укажите количество и подтвердите заказ.\n"
    f"3. Ожидайте подтверждения от нашего менеджера и доставки!\n\n"
    f"📌 <b>Внимание:</b> бот доступен только для жителей общежития №1.\n\n"
    f"Если возникли вопросы или предложения, пишите в нашу поддержку: <a href='https://t.me/EmilBAD'>t.me/EmilBAD</a>.\n\n"
    f"👉 Давайте сделаем ваш день бодрее вместе с &quot;<b>СС Маркет</b>&quot;! 🚀"
)

demo_quest = (f"Мы хотим узнать ваши предпочтения, чтобы сделать продажу энергетических напитков "
            f"в общежитии максимально удобной и интересной для вас. 💡\n\n"
            f"Пожалуйста, примите участие в опросе и выберите свои любимые напитки. "
            f"Это поможет нам понять, какие варианты стоит включить в ассортимент! 🛒\n\n"
            f"Опрос займет всего минуту, а ваш вклад сделает нашу небольшую торговлю лучше! 😊")

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

optionsDrink = ["Red Bull", "Gorilla", "Adrenaline Rush", "Flash", "LitEnergy", "LitEnergy(Только новые)", "Burn", "Volt", "Drive", "Jaguar"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Начать опрос", callback_data="opros")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=start_message, parse_mode="HTML")
    await context.bot.send_message(chat_id=update.effective_chat.id, text=demo_quest, reply_markup=reply_markup)

async def opros(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    print(completed_users)
    if user_id in completed_users:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Вы уже прошли опрос. Спасибо за участие! 😊"
        )
        return

    question = "Какие энергетики вы предпочитаете? (Можно выбрать несколько)"
    
    is_anonymous = False  # Сделать опрос неанонимным
    allows_multiple_answers = True  # Разрешить выбор нескольких вариантов

    await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=question,
        options=optionsDrink,
        is_anonymous=is_anonymous,
        allows_multiple_answers=allows_multiple_answers
    )
    user_id = update.effective_user.id
    completed_users.add(user_id)

async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global poll_results
    try:
        selected_options = set(update.poll_answer.option_ids)
        poll_results = {i: 0 for i in optionsDrink}
        print(poll_results)
        for option_id in selected_options:
            poll_results[optionsDrink[option_id]] += 1
        logging.info(f"Обновленные результаты {poll_results}")
    except AttributeError:
        logging.error("Ошибка при обработке ответа на опрос")


async def send_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global poll_results
    if update.effective_user.id not in ADMIN_ID:
        await update.message.reply_text("У вас нет прав для просмотра статистики.")
        return
    print(poll_results)
    if not poll_results:
        await update.message.reply_text("На данный момент нет результатов для отображения.")
        return

    stats_message = "📊 <b>Статистика опросов:</b>\n"
    stats_message += f"Кол-во проголосовавших: {len(completed_users)} \n"
    for poll_name, votes in poll_results.items():
        stats_message += f"Вариант {poll_name}: {100 * (float(votes)/float(len(completed_users))) if len(completed_users) != 0 and votes != 0 else 0}% голосов\n"
    
    await update.message.reply_text(stats_message, parse_mode="HTML")


if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    application.add_handler(PollAnswerHandler(handle_poll_answer))
    application.add_handler(CommandHandler("statistics", send_statistics))
    application.add_handler(CallbackQueryHandler(opros, pattern="^opros$"))
    
    application.run_polling()