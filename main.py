import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import TOKEN
from pyzbar.pyzbar import decode
from PIL import Image
import tempfile

logging.basicConfig(
    level=logging.INFO,  # Less verbose
    format='%(asctime)s - %(levelname)s - %(message)s'
)

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


ADMIN_IDS = [7376396301]
def is_admin(user_id):
    return user_id in ADMIN_IDS

#---STATES---
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

class SendToUserFSM(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_message = State()

class WiFiQRStates(StatesGroup):
    waiting_for_ssid = State()
    waiting_for_password = State()
#---End STATES---

#---PARSERS---
import re

def parse_wifi_qr(data: str):
    pattern = r'WIFI:T:(?P<security>[^;]*);S:(?P<ssid>[^;]*);P:(?P<password>[^;]*);;'
    match = re.match(pattern, data)
    if match:
        return match.groupdict()
    return None

#---End PARSERS---


from stats import add_user, get_user_by_id, get_user_count, get_users

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name

    existing_user = get_user_by_id(user_id)
    if not existing_user:
        add_user(user_id, username)
        await bot.send_message(
            ADMIN_IDS[0],
            f"**📥 New User Joined!**\n"
            f"🆔 ID: `{user_id}`\n"
            f"🔗 Username: @{username if username else 'None'}\n"
            f"👤 Name: {full_name}\n"
            f"📊 Total users: {get_user_count()}",
            parse_mode="HTML"
        )

    await message.reply(
        "Hey! 👋\n"
        "Send /generate <text> to get a QR code.\n"
        "Or send me a photo of a QR code to scan it!"
    )

@dp.message_handler(commands=['generate'])
async def generate_qr(message: types.Message):
    try:
        data = message.get_args()
        if not data:
            return await message.reply("❗ Usage: /generate <text>")
        img = qrcode.make(data)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            img.save(tmp.name)
            with open(tmp.name, "rb") as photo:
                await message.reply_photo(photo, caption="✅ Your QR code!")
        os.remove(tmp.name)
    except Exception as e:
        await message.reply(f"Error generating QR: {e}")

@dp.message_handler(content_types=['photo'])
async def scan_qr(message: types.Message):
    try:
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            await message.photo[-1].download(destination=tmp.name)
            path = tmp.name
            with Image.open(path) as img:
                decoded = decode(img)
        os.remove(path)

        if decoded:
            qr_data = decoded[0].data.decode('utf-8')

            # Check if it's a Wi-Fi QR
            wifi_match = re.match(r"WIFI:T:(?P<security>[^;]*);S:(?P<ssid>[^;]*);P:(?P<password>[^;]*);", qr_data)
            if wifi_match:
                wifi_info = wifi_match.groupdict()
                password_text = f"🔑 Password: `{wifi_info['password']}`" if wifi_info["password"] else "🔓 Open network"

                wifi_config = f"WIFI:T:{wifi_info['security']};S:{wifi_info['ssid']};P:{wifi_info['password']};;"

                keyboard = InlineKeyboardMarkup().add(
                    InlineKeyboardButton(text="📋 Copy Wi-Fi Config", switch_inline_query=wifi_config)
                )

                await message.reply(
                    f"📶 *Wi-Fi QR Code Detected:*\n\n"
                    f"🔹 SSID: `{wifi_info['ssid']}`\n"
                    f"{password_text}\n"
                    f"🔐 Security: `{wifi_info['security']}`",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
            else:
                await message.reply(f"📷 Scanned QR content:\n`{qr_data}`", parse_mode="Markdown")
        else:
            await message.reply("⚠️ No QR code detected in the image.")
    except Exception as e:
        await message.reply(f"Error scanning QR: {e}")



@dp.message_handler(commands=['send_to_user'])
async def send_to_user(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⚠️ You are not authorized to send messages to other users.")
        return
    try:
        parts = message.text.split(maxsplit=2)
        if len(parts) < 3:
            await message.reply("❗ Usage: /send_to_user <user_id> <message>")
            return
        user_id = int(parts[1])
        text = parts[2]
        await bot.send_message(user_id, text)
        await message.reply(f"✅ Message sent to user {user_id}")
    except Exception as e:
        await message.reply(f"Error sending message: {e}")

@dp.message_handler(commands=['stats'])
async def show_stats(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("⚠️ You are not authorized to view the stats.")
        return
    users_count = get_user_count()
    await message.reply(f"📊 Usage Stats:\n- Total users: {users_count}")

@dp.message_handler(commands=['broadcast'])
async def broadcast_cmd(message: types.Message):
    logging.debug(f"Broadcast command by user {message.from_user.id}")
    if message.from_user.id not in ADMIN_IDS:
        logging.warning(f"User {message.from_user.id} not admin")
        return await message.reply("⛔ You are not allowed to use this command.")
    logging.debug("Waiting for broadcast message")
    await message.reply("Send me the broadcast message (HTML format).")
    @dp.message_handler(lambda m: m.from_user.id == message.from_user.id)
    async def get_broadcast_content(msg: types.Message):
        logging.debug("Got broadcast message")
        users = get_users()
        logging.info(f"Users to broadcast: {users}")
        if not users:
            logging.warning("No users found")
            await msg.reply("⚠️ No users to broadcast to.")
            dp.message_handlers.unregister(get_broadcast_content)
            return
        success = 0
        for user_id in users:
            try:
                await bot.send_message(user_id, msg.text, parse_mode="HTML")
                success += 1
                logging.debug(f"Sent to {user_id}")
            except Exception as e:
                logging.warning(f"Failed to send to {user_id}: {e}")
        await msg.reply(f"✅ Broadcast sent to {success}/{len(users)} users.")
        dp.message_handlers.unregister(get_broadcast_content)


@dp.message_handler(commands=["admin"])
async def admin_panel(message: types.Message):
    user_id = message.from_user.id
    if not is_admin(user_id):
        await message.reply("❌ You are not authorized to access the admin panel.")
        logging.warning(f"Unauthorized access attempt to /admin by {user_id}")
        return

    logging.info(f"Admin panel opened by {user_id} (@{message.from_user.username})")

    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(text="📊 Stats", callback_data="stats"),
        InlineKeyboardButton(text="📢 Broadcast", callback_data="broadcast"),
        InlineKeyboardButton("✉️ Send to User", callback_data="send_to_user")
    )

    await message.reply("👑 Admin Panel", reply_markup=keyboard)


# Handle /stats action when the button is pressed
@dp.callback_query_handler(lambda c: c.data == "stats")
async def process_stats_callback(callback_query: types.CallbackQuery):
    users = get_users()
    total = len(users)
    text = f"📊 Total users: <b>{total}</b>"
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, text, parse_mode="HTML")
    logging.info(f"Stats shown to {callback_query.from_user.id} (@{callback_query.from_user.username})")



# Handle /broadcast action when the button is pressed
@dp.callback_query_handler(lambda c: c.data == "broadcast", state="*")
async def process_broadcast_callback(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await bot.send_message(callback_query.from_user.id, "Send the message to broadcast:")

    @dp.message_handler(lambda message: True, content_types=types.ContentTypes.TEXT)
    async def receive_broadcast_text(message: types.Message):
        users = get_users()
        logging.info(f"Broadcasting to users: {users}")

        count = 0
        for user_id in users:
            try:
                await bot.send_message(chat_id=user_id, text=message.text)
                count += 1
            except Exception as e:
                logging.warning(f"Failed to send to {user_id}: {e}")

        await bot.send_message(message.from_user.id, f"✅ Broadcast message sent to {count} users.")
        # Unregister handler so it doesn't keep triggering
        dp.message_handlers.unregister(receive_broadcast_text)

@dp.callback_query_handler(lambda c: c.data == "send_to_user")
async def start_send_to_user(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await SendToUserFSM.waiting_for_user_id.set()
    await bot.send_message(callback_query.from_user.id, "👤 Enter the user ID to send the message to:")

@dp.message_handler(state=SendToUserFSM.waiting_for_user_id)
async def get_user_id(message: types.Message, state: FSMContext):
    try:
        user_id = int(message.text.strip())
        await state.update_data(user_id=user_id)
        await SendToUserFSM.next()
        await message.answer("📝 Now enter the message you want to send:")
    except ValueError:
        await message.answer("❌ Invalid user ID. Please enter a number.")

@dp.message_handler(state=SendToUserFSM.waiting_for_message)
async def get_message_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("user_id")
    text = message.text

    try:
        await bot.send_message(user_id, text)
        await message.answer(f"✅ Message sent to <code>{user_id}</code>", parse_mode="HTML")
        logging.info(f"Message sent to {user_id} by {message.from_user.id}")
    except Exception as e:
        await message.answer(f"❌ Failed to send message: {e}")
        logging.error(f"Failed to send message to {user_id}: {e}")
    finally:
        await state.finish()

@dp.message_handler(commands=['wifiqr'])
async def wifi_qr_start(message: types.Message):
    logging.info(f"Starting Wi-Fi QR code creation for {message.from_user.id}")
    await message.answer("📶 Send the Wi-Fi name (SSID):")
    await WiFiQRStates.waiting_for_ssid.set()


@dp.message_handler(state=WiFiQRStates.waiting_for_ssid)
async def wifi_get_ssid(message: types.Message, state: FSMContext):
    logging.info(f"Received Wi-Fi name (SSID) from {message.from_user.id}: {message.text}")
    await state.update_data(ssid=message.text)
    await message.answer("🔒 Now send the Wi-Fi password:")
    await WiFiQRStates.waiting_for_password.set()

import qrcode

@dp.message_handler(state=WiFiQRStates.waiting_for_password)
async def wifi_get_password(message: types.Message, state: FSMContext):
    data = await state.get_data()
    ssid = data['ssid']
    password = message.text

    logging.info(f"Received Wi-Fi password from {message.from_user.id}")

    qr_data = f"WIFI:T:WPA;S:{ssid};P:{password};;"
    img = qrcode.make(qr_data)
    bio = BytesIO()
    bio.name = "wifi_qr.png"
    img.save(bio, 'PNG')
    bio.seek(0)

    await bot.send_photo(message.chat.id, photo=bio, caption="📡 Your Wi-Fi QR Code is ready!")
    logging.info(f"Sent Wi-Fi QR code to {message.from_user.id}")
    await state.finish()

cached_file_ids = {}

from io import BytesIO

import hashlib
from aiogram.types import InlineQueryResultPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.exceptions import TelegramAPIError


@dp.inline_handler()
async def inline_qr_handler(inline_query: types.InlineQuery):
    qr_text = inline_query.query.strip()

    if len(qr_text) >= 3:
        try:
            if len(qr_text) > 1000:
                await bot.answer_inline_query(
                    inline_query.id,
                    results=[],
                    cache_time=1,
                    switch_pm_text="Text too long! Try shorter text.",
                    switch_pm_parameter="error"
                )
                return
            img = qrcode.make(qr_text)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                img.save(tmp.name)
                path = tmp.name
            with open(path, "rb") as photo:
                # Send to admin chat and delete immediately
                message = await bot.send_photo(
                    chat_id=ADMIN_IDS[0],  # Your admin ID (7376396301)
                    photo=types.InputFile(path),
                    caption="Temporary QR code upload"
                )
                file_id = message.photo[-1].file_id
                # Delete the message to avoid clutter
                await bot.delete_message(
                    chat_id=ADMIN_IDS[0],
                    message_id=message.message_id
                )
            os.remove(path)
            result_id = hashlib.md5(qr_text.encode()).hexdigest()
            await bot.answer_inline_query(
                inline_query.id,
                results=[
                    InlineQueryResultPhoto(
                        id=result_id,
                        photo_url=file_id,
                        thumb_url=f"https://api.telegram.org/file/bot{TOKEN}/{file_id}",
                        caption=f"QR code for: {qr_text[:50]}...",
                    )
                ],
                cache_time=60
            )
        except TelegramAPIError as e:
            logging.error(f"Telegram API error in inline QR: {e}")
            await bot.answer_inline_query(inline_query.id, results=[], cache_time=1)
        except Exception as e:
            logging.error(f"Error generating inline QR: {e}")
            await bot.answer_inline_query(inline_query.id, results=[], cache_time=1)
    else:
        await bot.answer_inline_query(
            inline_query.id,
            results=[],
            cache_time=1,
            switch_pm_text="Type at least 3 characters to generate a QR code",
            switch_pm_parameter="start"
        )



#---BOT START---
async def set_default_commands(dp):
    await dp.bot.set_my_commands([
        types.BotCommand("start", "Start the bot"),
        types.BotCommand("help", "Show help message"),
        types.BotCommand("generate", "Generate QR code"),
        types.BotCommand("scan", "Scan QR from photo"),
        types.BotCommand("wifiqr", "Create Wi-Fi QR code"),
        types.BotCommand("admin", "Admin panel"),
    ])

async def on_startup(dp):
    logging.info("Starting bot...")
    await bot.send_message(ADMIN_IDS[0], "Bot started!")
    await set_default_commands(dp)


if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, on_startup=on_startup, skip_updates=True)