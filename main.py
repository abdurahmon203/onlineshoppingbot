from telebot.async_telebot import AsyncTeleBot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import asyncio

import db
bot = AsyncTeleBot("8726151482:AAEow-CyXYl2ElAKKXd9uWqwNmvIuEv9KhU")
GROUP_ID = -1003791002710

qty_cache = {}

TEXT = {
    "tj": {
        "start": "🛒 Маҳз фурӯш оғоз шуд",
        "help": "📖 ЁРӢ",
        "language": "🌐 Забон интихоб кунед",
        "products": "🛒 Маҳсулотҳо",
        "cart": "🧺 Сабад",
        "orders": "📦 Заказҳо",
        "history": "📦 Таърих",
        "loading": "⏳ Боркунӣ...",
        "empty_cart": "🧺 Сабад холӣ",
        "empty_history": "📦 Таърих холӣ",
        "added": "🧺 Ба сабад илова шуд",
        "checkout": "💳 Харидан",
        "done": "📦 Заказ фиристода шуд!",
        "plus": "➕",
        "minus": "➖",
        "add": "🧺 Илова кардан",
    },
    "ru": {
        "start": "🛒 Магазин открыт",
        "help": "📖 Помощь",
        "language": "🌐 Выбор языка",
        "products": "🛒 Товары",
        "cart": "🧺 Корзина",
        "orders": "📦 Заказы",
        "history": "📦 История",
        "loading": "⏳ Загрузка...",
        "empty_cart": "🧺 Корзина пуста",
        "empty_history": "📦 История пуста",
        "added": "🧺 Добавлено",
        "checkout": "💳 Оформить заказ",
        "done": "📦 Заказ отправлен!",
        "plus": "➕",
        "minus": "➖",
        "add": "🧺 В корзину",
    },
}


async def t(uid):
    lang = await db.get_lang(uid)
    return TEXT.get(lang, TEXT["tj"])


def product_kb(pid, qty, tr):
    kb = InlineKeyboardMarkup(row_width=3)

    kb.add(
        InlineKeyboardButton(tr["minus"], callback_data=f"minus_{pid}"),
        InlineKeyboardButton(str(qty), callback_data="noop"),
        InlineKeyboardButton(tr["plus"], callback_data=f"plus_{pid}"),
    )

    kb.add(InlineKeyboardButton(tr["add"], callback_data=f"cart_{pid}"))
    return kb


@bot.message_handler(commands=["start"])
async def start(message):
    await db.add_user(message.from_user.id, message.from_user.first_name)

    tr = await t(message.from_user.id)

    await bot.send_message(message.chat.id, tr["start"])
    await send_products(message.chat.id, message.from_user.id)


@bot.message_handler(commands=["help"])
async def help_cmd(message):
    tr = await t(message.from_user.id)

    text = f"""
{tr['help']}

/start - {tr['start']}
/help - {tr['help']}
/language - {tr['language']}
/products - {tr['products']}
/cart - {tr['cart']}
/orders - {tr['orders']}
/history - {tr['history']}
"""
    await bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["language"])
async def language(message):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("🇹🇯 TJ", callback_data="lang_tj"),
        InlineKeyboardButton("🇷🇺 RU", callback_data="lang_ru"),
    )

    tr = await t(message.from_user.id)
    await bot.send_message(message.chat.id, tr["language"], reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data.startswith("lang_"))
async def language_handler(call):
    lang = call.data.split("_")[1]

    await db.set_lang(call.from_user.id, lang)

    tr = await t(call.from_user.id)
    await bot.answer_callback_query(call.id, tr["language"])


@bot.message_handler(commands=["products"])
async def products_cmd(message):
    tr = await t(message.from_user.id)
    await bot.send_message(message.chat.id, tr["loading"])
    await send_products(message.chat.id, message.from_user.id)


async def send_products(chat_id, uid):
    products = await db.get_products()
    tr = await t(uid)

    for p in products:
        pid = p["id"]

        if pid not in qty_cache:
            qty_cache[pid] = 1

        await bot.send_photo(
            chat_id,
            p["avatar"],
            caption=f"{p['name']}\n💰 {p['price']}",
            reply_markup=product_kb(pid, qty_cache[pid], tr),
        )


@bot.callback_query_handler(
    func=lambda c: c.data.startswith("plus_") or c.data.startswith("minus_")
)
async def qty_handler(call):
    tr = await t(call.from_user.id)

    action, pid = call.data.split("_")
    pid = int(pid)

    qty_cache[pid] = qty_cache.get(pid, 1)

    if action == "plus":
        qty_cache[pid] += 1
    else:
        qty_cache[pid] = max(1, qty_cache[pid] - 1)

    await bot.edit_message_reply_markup(
        call.message.chat.id,
        call.message.message_id,
        reply_markup=product_kb(pid, qty_cache[pid], tr),
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("cart_"))
async def cart_add(call):
    tr = await t(call.from_user.id)

    pid = int(call.data.split("_")[1])
    qty = qty_cache.get(pid, 1)

    await db.add_to_cart(call.from_user.id, pid, qty)

    await bot.answer_callback_query(call.id, tr["added"])


@bot.message_handler(commands=["cart"])
async def cart_view(message):
    tr = await t(message.from_user.id)

    data = await db.get_cart(message.from_user.id)

    if not data:
        return await bot.send_message(message.chat.id, tr["empty_cart"])

    text = "🧺 CART:\n\n"
    total = 0

    for r in data:
        sum_ = r["price"] * r["quantity"]
        total += sum_
        text += f"{r['name']} x{r['quantity']} = {sum_}\n"

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton(tr["checkout"], callback_data="checkout"))

    await bot.send_message(message.chat.id, text + f"\nTOTAL: {total}", reply_markup=kb)


@bot.callback_query_handler(func=lambda c: c.data == "checkout")
async def checkout(call):
    tr = await t(call.from_user.id)

    user_id = call.from_user.id
    cart = await db.get_cart(user_id)

    if not cart:
        return await bot.answer_callback_query(call.id, tr["empty_cart"])

    msg = f"📦 ORDER\nUser: {user_id}\n\n"
    total = 0

    for r in cart:
        sum_ = r["price"] * r["quantity"]
        total += sum_
        msg += f"{r['name']} x{r['quantity']} = {sum_}\n"

    msg += f"\nTOTAL: {total}"

    await db.save_orders(user_id)
    await db.clear_cart(user_id)

    await bot.send_message(GROUP_ID, msg)

    await bot.answer_callback_query(call.id, tr["done"])
    await bot.send_message(call.message.chat.id, tr["done"])


@bot.message_handler(commands=["history", "orders"])
async def history(message):
    tr = await t(message.from_user.id)

    data = await db.get_orders(message.from_user.id)

    if not data:
        return await bot.send_message(message.chat.id, tr["empty_history"])

    text = "📦 HISTORY:\n\n"

    for r in data:
        text += f"{r['name']} x{r['quantity']} = {r['price'] * r['quantity']}\n"

    await bot.send_message(message.chat.id, text)


async def main():
    await db.create_tables()
    print("BOT RUNNING...")
    await bot.infinity_polling()


asyncio.run(main())
