"""Telegram bot: event selection, admin commands and durable upload worker."""
import asyncio
import logging
import mimetypes
import os
import re
import tempfile
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, ApplicationBuilder, CallbackQueryHandler, CommandHandler,
    ContextTypes, MessageHandler, filters,
)
from app.db import Store
from app import drive

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger(__name__)
load_dotenv()
SETTINGS = dict(os.environ)
DATA_DIR = Path(SETTINGS.get("DATA_DIR", "./data"))
STORE = Store(str(DATA_DIR))
ADMIN_IDS = {int(x) for x in SETTINGS.get("ADMIN_TELEGRAM_IDS", "").split(",") if x.strip().isdigit()}


def admin(update: Update):
    return bool(update.effective_user and update.effective_user.id in ADMIN_IDS)


def menu():
    events = STORE.active_events()
    if not events:
        return None
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f'{e["event_date"]} · {e["name"]}', callback_data=f'event:{e["id"]}')]
        for e in events[:90]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Вітаємо! Виберіть подію. Після цього надсилайте фото, відео або файли.\n"
        "Для оригінальної якості фото надсилайте як файл.",
        reply_markup=menu()
    )


async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Ваш Telegram ID: {update.effective_user.id}")


async def events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Оберіть подію:", reply_markup=menu())


async def choose(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        event_id = int(query.data.split(":", 1)[1])
    except (ValueError, IndexError):
        await query.answer("Помилкова подія", show_alert=True)
        return
    if STORE.select(query.from_user.id, event_id):
        selected = STORE.get_event(event_id)
        await query.answer()
        await query.edit_message_text(
            f'Обрано: {selected["name"]} ({selected["event_date"]}).\n'
            "Тепер надсилайте фото, відео або документи. Для зміни події: /events"
        )
    else:
        await query.answer("Подія недоступна. Натисніть /events", show_alert=True)


async def add_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin(update):
        await update.message.reply_text("Доступ лише адміністратору.")
        return
    parts = update.message.text.split(maxsplit=2)
    if len(parts) < 3:
        await update.message.reply_text("Формат: /add_event YYYY-MM-DD Назва події")
        return
    try:
        event_day = date.fromisoformat(parts[1])
        if event_day.isoformat() != parts[1]:
            raise ValueError()
    except ValueError:
        await update.message.reply_text("Дата має бути у форматі YYYY-MM-DD.")
        return
    name = parts[2].strip()
    if not name or len(name) > 100:
        await update.message.reply_text("Назва повинна мати від 1 до 100 символів.")
        return
    try:
        folder = await asyncio.to_thread(drive.create_event_folder, SETTINGS, parts[1], name)
        event_id = STORE.add_event(name, parts[1], folder)
        await update.message.reply_text(f"✅ Створено подію #{event_id}: {name}")
    except Exception:
        log.exception("Failed to create event")
        await update.message.reply_text("Не вдалося створити папку в Google Drive. Перевірте конфігурацію.")


async def close_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not admin(update):
        await update.message.reply_text("Доступ лише адміністратору.")
        return
    args = context.args
    if len(args) != 1 or not args[0].isdigit():
        await update.message.reply_text("Формат: /close_event ID")
        return
    closed = STORE.close_event(int(args[0]))
    await update.message.reply_text("✅ Подію закрито." if closed else "Активної події з таким ID немає.")


def media_info(message):
    if message.photo:
        photo = message.photo[-1]
        return photo.file_id, f"photo_{message.message_id}.jpg", "image/jpeg"
    media = message.video or message.document
    if not media:
        return None
    filename = getattr(media, "file_name", None) or f"media_{message.message_id}"
    filename = re.sub(r'[/\\\x00-\x1f]+', "_", filename)[:180]
    kind = getattr(media, "mime_type", None) or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return media.file_id, filename, kind


async def receive(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or message.chat.type != "private":
        return
    event = STORE.selected_event(message.from_user.id)
    if event is None:
        await message.reply_text("Спочатку виберіть подію: /events")
        return
    payload = media_info(message)
    if payload is None:
        return
    added = STORE.enqueue(message.chat.id, message.message_id, message.from_user.id,
                          event["id"], *payload)
    await message.reply_text("📥 Файл прийнято в чергу." if added else "Цей файл уже прийнято.")


async def worker(application: Application):
    while True:
        job = STORE.next_job()
        if job is None:
            await asyncio.sleep(2)
            continue
        path = None
        try:
            file = await application.bot.get_file(job["telegram_file_id"])
            fd, path = tempfile.mkstemp(prefix="upload_", dir=str(DATA_DIR))
            os.close(fd)
            await file.download_to_drive(custom_path=path)
            drive_id = await asyncio.to_thread(
                drive.upload, SETTINGS, path, job["folder_id"], job["filename"], job["mime_type"]
            )
            STORE.completed(job["id"], drive_id)
            await application.bot.send_message(job["chat_id"], f'✅ Збережено: {job["filename"]}')
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log.exception("Upload job %s failed", job["id"])
            retry = job["attempts"] < 3
            STORE.failed(job["id"], type(exc).__name__ + ": " + str(exc), retry)
            if not retry:
                try:
                    await application.bot.send_message(
                        job["chat_id"], "❌ Завантажити файл не вдалося. Зверніться до адміністратора."
                    )
                except Exception:
                    log.exception("Cannot send failure notice")
            else:
                await asyncio.sleep(min(30, 2 ** job["attempts"]))
        finally:
            if path:
                Path(path).unlink(missing_ok=True)


async def post_init(application: Application):
    application.bot_data["worker_task"] = asyncio.create_task(worker(application))


async def post_shutdown(application: Application):
    task = application.bot_data.get("worker_task")
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


def main():
    token = SETTINGS.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is missing")
    builder = ApplicationBuilder().token(token).post_init(post_init).post_shutdown(post_shutdown)
    if SETTINGS.get("TELEGRAM_LOCAL_API_URL"):
        builder = builder.base_url(SETTINGS["TELEGRAM_LOCAL_API_URL"])
        builder = builder.base_file_url(SETTINGS["TELEGRAM_LOCAL_FILE_URL"]).local_mode(True)
    application = builder.build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("events", events))
    application.add_handler(CommandHandler("myid", myid))
    application.add_handler(CommandHandler("add_event", add_event))
    application.add_handler(CommandHandler("close_event", close_event))
    application.add_handler(CallbackQueryHandler(choose, pattern=r"^event:\d+$"))
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & (
        filters.PHOTO | filters.VIDEO | filters.Document.ALL), receive))
    application.run_polling()


if __name__ == "__main__":
    main()
