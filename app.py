from dotenv import load_dotenv
import os
import json
import logging
from telegram import Update, Bot, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler,  CallbackContext, ConversationHandler, PollHandler, PollAnswerHandler, MessageHandler, filters, CallbackQueryHandler, MessageHandler

load_dotenv()
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = [833046485]
WAITING_FOR_ITEM_NUMBER = 1
AGE_CONFIRM_KEYBOARD = [["Мне есть 18 лет"], ["Мне нет 18 лет"]]
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
    f"👉 Давайте сделаем ваш день бодрее вместе с &quot;<b>СС Маркет</b>&quot;!🚀 \n\n"
    f"<b>Для покупки перейдите к ассортименту → Добавьте товары в корзину → Корзина → Оплата</b>"
)

# demo_quest = (f"Мы хотим узнать ваши предпочтения, чтобы сделать продажу энергетических напитков "
#             f"в общежитии максимально удобной и интересной для вас. 💡\n\n"
#             f"Пожалуйста, примите участие в опросе и выберите свои любимые напитки. "
#             f"Это поможет нам понять, какие варианты стоит включить в ассортимент! 🛒\n\n"
#             f"Опрос займет всего минуту, а ваш вклад сделает нашу небольшую торговлю лучше! 😊")



logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

optionsDrink = ["Red Bull", "Gorilla", "Adrenaline Rush", "Flash", "LitEnergy", "LitEnergy(Только новые)", "Burn", "Volt", "Drive", "Jaguar"]

BUYKEYBOARD = [["К ассортименту", "Корзина"], ["Баллы","Тех.поддержка"]]
CARTKEYBOARD = [["Оплата", "К ассортименту"],["Удалить товар", "Очистить всю корзину"]]

USERS_FILE = "users.json"

# Загрузка пользователей из файла
def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data.get("chat_ids", [])  # Возвращаем список chat_id
    except (FileNotFoundError, json.JSONDecodeError):
        return []  # Если файла нет или он повреждён, возвращаем пустой список

# Сохранение пользователей в файл
def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as file:
        json.dump({"chat_ids": users}, file, ensure_ascii=False, indent=4)

# Добавление нового пользователя
def add_user(chat_id):
    users = load_users()
    if chat_id not in users:
        users.append(chat_id)
        save_users(users)

def open_json():
    with open("drinks.json", "r", encoding="utf-8") as file:
        return json.load(file)

def save_drinks(data):
    with open("drinks.json", "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

DRINKS = open_json()

def calculate_total(cart: dict) -> int:
    global DRINKS, total
    data = DRINKS
    total = 0
    for brand, flavors in cart.items():
        for flavor, quantity in flavors.items():
            # Находим цену из DRINKS
            price = data["drinks"][brand]["flavors"][flavor]["price"]
            total += price * quantity
    return total

async def clear_cart_after_timeout(context: CallbackContext):
    chat_id = context.job.chat_id
    context.user_data.pop("cart", None)
    await context.bot.send_message(chat_id=chat_id, text="Ваша корзина была очищена через 5 минут.")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    chat_id = update.message.chat_id

    # Загрузка списка пользователей
    users = load_users()

    # Добавляем нового пользователя, если его ещё нет в списке
    if chat_id not in users:
        add_user(chat_id)
    keyboard = [
        [InlineKeyboardButton("Начать опрос", callback_data="opros")]
    ]
    reply_markup = ReplyKeyboardMarkup(BUYKEYBOARD, resize_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=start_message, reply_markup=reply_markup, parse_mode="HTML")
    reply_markup = ReplyKeyboardMarkup(AGE_CONFIRM_KEYBOARD, resize_keyboard=True, one_time_keyboard=True)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "⚠️ Вы должны быть старше 18 лет для использования этого бота.\n"
            "Создатели бота не несут ответственности за ваши действия, связанные с использованием бота.\n\n"
            "Подтвердите, пожалуйста, ваш возраст:"
        ),
        reply_markup=reply_markup,
    )

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global DRINKS
    if not context.user_data.get('age_confirmed', False):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Сначала подтвердите свой возраст, выбрав один из предложенных вариантов."
        )
        return
    data = DRINKS
    global current_brand, current_flavor, total
    keyboard = [
        [InlineKeyboardButton(drink, callback_data=f"producer:{drink}:0") for drink in data["drinks"]]
    ]
    reply_markup = ReplyKeyboardMarkup(BUYKEYBOARD, resize_keyboard=True)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Ассортимент:", reply_markup=reply_markup)
    reply_markup = InlineKeyboardMarkup(keyboard)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Выберите производителя:", reply_markup=reply_markup)
    
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if 'age_confirmed' not in context.user_data:
        if text == "Мне есть 18 лет":
            context.user_data['age_confirmed'] = True  # Устанавливаем флаг подтверждения
            reply_markup = ReplyKeyboardMarkup(BUYKEYBOARD, resize_keyboard=True)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Спасибо за подтверждение. Добро пожаловать! 😊",
                reply_markup=reply_markup
            )

        elif text == "Мне нет 18 лет":
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="К сожалению, вы не можете использовать этот бот. До свидания!"
            )
            return

        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Пожалуйста, выберите один из предложенных вариантов."
            )
    if not context.user_data.get('age_confirmed', False):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Сначала подтвердите свой возраст, выбрав один из предложенных вариантов."
        )
        return
    if text == "К ассортименту":
        await buy(update, context)
    elif text == "Корзина":
        reply_markup = ReplyKeyboardMarkup(CARTKEYBOARD, resize_keyboard=True)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="🛒 Ваши товары в корзине:", reply_markup=reply_markup)
        await show_cart(update, context)
    elif text == "Тех.поддержка":
        reply_markup = ReplyKeyboardMarkup(BUYKEYBOARD, resize_keyboard=True)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Обратиться: t.me/EmilBAD", reply_markup=reply_markup)
    elif text == "Баллы":
        reply_markup = ReplyKeyboardMarkup(BUYKEYBOARD, resize_keyboard=True)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Пока недоступно", reply_markup=reply_markup)
    elif text == "Очистить всю корзину":
        await clear_cart(update, context, DRINKS)
    elif text == "Удалить товар":
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Введите номер товара из корзины для удаления.")
        return WAITING_FOR_ITEM_NUMBER  # Переводим в состояние ожидания ввода
    elif text == "Оплата":
        await process_payment(update, context)

async def clear_cart(update, context, data_j):
    if not context.user_data.get('age_confirmed', False):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Сначала подтвердите свой возраст, выбрав один из предложенных вариантов."
        )
        return
    cart = context.user_data.pop("cart", {})
    print(cart)
    for brand, flavors in cart.items():
        for flavor, quantity in flavors.items():
            if brand in data_j["drinks"] and flavor in data_j["drinks"][brand]["flavors"]:
                data_j["drinks"][brand]["flavors"][flavor]["quantity"] += quantity

    await context.bot.send_message(chat_id=update.effective_chat.id, text="Корзина очищена.")

async def process_payment(update: Update, context: CallbackContext):
    if not context.user_data.get('age_confirmed', False):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Сначала подтвердите свой возраст, выбрав один из предложенных вариантов."
        )
        return
    """Обработка нажатия на кнопку 'Оплата'."""
    cart = context.user_data.get("cart", {})

    if not cart:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Ваша корзина пуста. Добавьте товары перед оплатой."
        )
        return

    total = calculate_total(cart)

    payment_text = (
        f"💳 Для оплаты переведите сумму {total}₽ на номер телефона Тинькофф: +79534032798.\n"
        f"Эмиль Б.\n"
        f"⚠️ Нажимайте кнопку 'Оплатил' только после перевода!"
    )

    payment_keyboard = ReplyKeyboardMarkup([
        ["Оплатил", "Отмена"]
    ], resize_keyboard=True, one_time_keyboard=True)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=payment_text,
        reply_markup=payment_keyboard
    )

async def handle_payment_confirmation(update: Update, context: CallbackContext):
    if not context.user_data.get('age_confirmed', False):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Сначала подтвердите свой возраст, выбрав один из предложенных вариантов."
        )
        return
    """Обработка подтверждения оплаты."""
    text = update.message.text
    print(text)

    if text == "Оплатил":
        cart = context.user_data.get("cart", {})
        total = calculate_total(cart)
        chat_id = update.effective_chat.id

        cart_details = "\n".join([
            f"{brand} - {flavor}: {quantity} шт."
            for brand, flavors in cart.items()
            for flavor, quantity in flavors.items()
        ])

        admin_message = (
            f"💰 Новый заказ от пользователя {chat_id}:\n"
            f"{cart_details}\n"
            f"Сумма заказа: {total}₽"
        )

        for admin_id in ADMIN_ID:
            await context.bot.send_message(chat_id=admin_id, text=admin_message)

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Спасибо за оплату! Можете забрать заказ в 217 комнате",
            reply_markup=ReplyKeyboardMarkup(BUYKEYBOARD, resize_keyboard=True)
        )

        # Очищаем корзину после подтверждения
        context.user_data.pop("cart", None)

    elif text == "Отмена":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Оплата отменена.",
            reply_markup=ReplyKeyboardMarkup(BUYKEYBOARD, resize_keyboard=True)
        )


async def send_taste_messages(update: Update, context: CallbackContext, arg: str):
    if not context.user_data.get('age_confirmed', False):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Сначала подтвердите свой возраст, выбрав один из предложенных вариантов."
        )
        return
    global DRINKS
    data_j = DRINKS

    if "message_key" not in context.user_data:
        context.user_data["message_key"] = {}

    message_key = 0

    for taste, taste_info in data_j["drinks"][arg]["flavors"].items():
        text = f"{taste} - {taste_info['price']}р\nКол-во: {taste_info['quantity']}шт"
        callback_data = f"taste:{taste}:{arg}"
        image_url = taste_info.get("image_url", None)  # Получаем ссылку на изображение из JSON

        if int(taste_info['quantity']) > 0:
            # Кнопки для активного состояния
            keyboard = [
                [InlineKeyboardButton("Добавить в корзину", callback_data=callback_data)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            # Неактивные кнопки для старых сообщений
            inactive_keyboard = [
                [InlineKeyboardButton("Неактивно", callback_data="none")]
            ]
            inactive_markup = InlineKeyboardMarkup(inactive_keyboard)

            if "message_key" in context.user_data and message_key in context.user_data["message_key"]:
                message_id = context.user_data["message_key"][message_key]
                try:
                    # Обновляем старое сообщение с неактивными кнопками
                    await context.bot.edit_message_reply_markup(
                        chat_id=update.effective_chat.id,
                        message_id=message_id,
                        reply_markup=inactive_markup
                    )
                except Exception as e:
                    print(f"Ошибка при отключении кнопок: {e}")

            # Отправляем изображение, если URL указан
            if image_url:
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=image_url,
                    caption=text,
                    reply_markup=reply_markup
                )
            else:
                # Отправляем сообщение без изображения
                message = await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=text,
                    reply_markup=reply_markup
                )

            # Сохраняем ID нового сообщения
            if "message_key" not in context.user_data:
                context.user_data["message_key"] = {}

            context.user_data["message_key"][message_key] = message_key
            message_key += 1


async def update_taste_message(update: Update, context: CallbackContext, brand: str, taste: str):
    if not context.user_data.get('age_confirmed', False):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Сначала подтвердите свой возраст, выбрав один из предложенных вариантов."
        )
        return
    global DRINKS
    data_j = DRINKS
    taste_info = data_j["drinks"][brand]["flavors"][taste]
    new_quantity = taste_info["quantity"]
    price = taste_info["price"]

    if "message_ids" not in context.user_data:
        context.user_data["message_ids"] = {}

    # Обновляем текст и количество товара в сообщении
    text = f"{taste} - {price}р\nКол-во: {new_quantity}шт"
    callback_data = f"taste:{taste}:{brand}"

    # Кнопка для добавления в корзину
    keyboard = [
        [InlineKeyboardButton("Добавить в корзину", callback_data=callback_data)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Обновляем сообщение, если оно существует
    message_id = context.user_data["message_ids"].get((brand, taste))
    if message_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup
            )
        except Exception as e:
            print(f"Ошибка при обновлении сообщения: {e}")


async def handle_buy(update: Update, context: CallbackContext):
    if not context.user_data.get('age_confirmed', False):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Сначала подтвердите свой возраст, выбрав один из предложенных вариантов."
        )
        return
    global current_brand, current_flavor
    query = update.callback_query
    await query.answer()
    data = query.data
    command, arg, arg2 = data.split(':')
    if command == "producer":
        await send_taste_messages(update, context, arg)
    elif command == "taste":
        current_brand = arg2
        current_flavor = arg
        await add_to_cart(update, context, arg, arg2)


async def add_to_cart(update: Update, context: CallbackContext, flavor: str, brand: str):
    if not context.user_data.get('age_confirmed', False):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Сначала подтвердите свой возраст, выбрав один из предложенных вариантов."
        )
        return
    global DRINKS, total
    data_j = DRINKS
    drink_data = data_j["drinks"][brand]["flavors"][flavor]
    if drink_data["quantity"] > 0:
        drink_data["quantity"] -= 1
        save_drinks(DRINKS)
        cart = context.user_data.setdefault("cart", {})
        cart[brand] = cart.get(brand, {})
        cart[brand][flavor] = cart[brand].get(flavor, 0) + 1

        total = calculate_total(cart)

        await update_taste_message(update, context, brand, flavor)

        # Добавляем сообщение о корзине
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Добавлено в корзину: {brand} - {flavor}\nОбщая сумма: {total}₽"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"К сожалению, {brand} - {flavor} закончился."
        )


async def show_cart(update: Update, context: CallbackContext):
    if not context.user_data.get('age_confirmed', False):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Сначала подтвердите свой возраст, выбрав один из предложенных вариантов."
        )
        return
    cart = context.user_data.get("cart", {}) 
    if not cart:
        message = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Ваша корзина пуста."
        )
        return

    cart_text = "\n"
    total = 0
    item_number = 1
    item_mapping = {}

    for brand, flavors in cart.items():
        for flavor, quantity in flavors.items():
            if quantity > 0:
                price_per_unit = DRINKS["drinks"][brand]["flavors"][flavor]["price"]
                total += price_per_unit * quantity
                cart_text += (
                    f"{item_number}. {brand} - {flavor}\n"
                    f"   Цена: {price_per_unit}₽, Кол-во: {quantity}\n"
                )
                item_mapping[item_number] = (brand, flavor)
                item_number += 1

    cart_text += f"\nОбщая сумма: {total}₽"

    # Сохраняем маппинг номера к товару в user_data
    context.user_data["item_mapping"] = item_mapping

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=cart_text
    )


async def remove_item_from_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('age_confirmed', False):
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Сначала подтвердите свой возраст, выбрав один из предложенных вариантов."
        )
        return
    global WAITING_FOR_ITEM_NUMBER
    user_input = update.message.text

    # Проверяем, что пользователь ввел число
    if user_input.isdigit():
        item_number = int(user_input)
        await remove_by_number(update, context, item_number)
        await update.message.reply_text("Товар успешно удален из корзины!")
    else:
        await update.message.reply_text("Пожалуйста, введите корректный номер товара.")
        return WAITING_FOR_ITEM_NUMBER  # Остаемся в состоянии ожидания

    return ConversationHandler.END  # Завершаем диалог

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Удаление товара отменено.")
    return ConversationHandler.END

remove_item_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.TEXT & filters.Regex("Удалить товар"), handle_text)],
    states={
        WAITING_FOR_ITEM_NUMBER: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_item_from_cart)],
    },
    fallbacks=[MessageHandler(filters.COMMAND, cancel)],
)


async def remove_by_number(update: Update, context: CallbackContext, item_number: int):
    cart = context.user_data.get("cart", {})
    item_mapping = context.user_data.get("item_mapping", {})

    # Проверяем, существует ли товар под указанным номером
    if item_number not in item_mapping:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Неверный номер товара. Проверьте корзину и попробуйте снова."
        )
        return

    # Получаем данные товара
    brand, flavor = item_mapping[item_number]

    if cart[brand][flavor] > 0:
        cart[brand][flavor] -= 1

        # Возвращаем товар на склад
        DRINKS["drinks"][brand]["flavors"][flavor]["quantity"] += 1
        save_drinks(DRINKS)

        # Удаляем товар из корзины, если количество стало 0
        if cart[brand][flavor] == 0:
            del cart[brand][flavor]
            if not cart[brand]:
                del cart[brand]

        total = calculate_total(cart)

        # Обновляем нумерацию
        await show_cart(update, context)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Удалён 1 шт. товара: {brand} - {flavor}\nОбщая сумма: {total}₽"
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Этого товара больше нет в вашей корзине."
        )

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()

    start_handler = CommandHandler('start', start)
    buy_handler = CommandHandler('buy', buy)
    cart_handler = CommandHandler('cart', show_cart)

    # Обработчик команды /start (всегда на первом месте)
    application.add_handler(start_handler)

    # Основные обработчики (будут работать после подтверждения возраста)
    application.add_handler(buy_handler, group=0)
    application.add_handler(cart_handler, group=0)
    application.add_handler(remove_item_handler, group=0)
    application.add_handler(CallbackQueryHandler(handle_buy), group=0)
    application.add_handler(MessageHandler(filters.Regex("^Оплатил$"), handle_payment_confirmation), group=0)
    application.add_handler(MessageHandler(filters.Regex("^Отмена$"), handle_payment_confirmation), group=0)
    application.add_handler(MessageHandler(filters.Regex("^Оплата$"), process_payment), group=0)

    # Общий обработчик текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text), group=0)

    application.run_polling()