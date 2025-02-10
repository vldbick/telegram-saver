import os
import time
import tempfile
import asyncio
import hashlib
import shutil
import logging
import yt_dlp
from aiogram import Bot
from aiogram.types import FSInputFile

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Максимальный размер файла для Telegram (50 МБ)
MAX_FILE_SIZE = 50 * 1024 * 1024

def generate_url_id(url: str) -> str:
    """Генерирует уникальный ID для URL."""
    return hashlib.md5(url.encode()).hexdigest()

def select_best_format(formats: list, socNet: str) -> str:
    """
    Выбирает лучший формат в зависимости от соцсети.
    :param formats: Список доступных форматов.
    :param socNet: Соцсеть (например, "tiktok", "youtube").
    :return: Лучший формат или None.
    """
    if socNet == "tiktok":
        # Для TikTok выбираем формат с видео и аудио
        best_format = max(
            (f for f in formats if f.get("vcodec") != "none" and f.get("acodec") != "none"),
            key=lambda f: (f.get("tbr") or 0),  # Если tbr = None, ставим 0
            default=None
        )
        return best_format["format_id"] if best_format else None

    elif socNet == "youtube":
        # Для YouTube выбираем лучшее видео и аудио
        video_formats = [f for f in formats if f.get("vcodec") != "none" and f.get("acodec") == "none"]
        audio_formats = [f for f in formats if f.get("vcodec") == "none" and f.get("acodec") != "none"]

        best_video = max(video_formats, key=lambda f: (f.get("height") or 0, f.get("vbr") or 0), default=None)
        best_audio = max(audio_formats, key=lambda f: (f.get("abr") or 0), default=None)

        if best_video and best_audio:
            return f"{best_video['format_id']}+{best_audio['format_id']}"
        else:
            return None

    else:
        # Для других соцсетей выбираем первый доступный формат
        return formats[0]["format_id"] if formats else None

async def download_media(url: str, format_id: str, output_path: str) -> str:
    """
    Скачивает медиафайл с указанным форматом.
    :param url: Ссылка на медиафайл.
    :param format_id: ID формата для скачивания.
    :param output_path: Путь для сохранения файла.
    :return: Путь к скачанному файлу.
    """
    ydl_opts = {
        'format': format_id,
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = await asyncio.to_thread(ydl.extract_info, url, download=True)
        return info.get("requested_downloads", [{}])[0].get("filepath", output_path)

async def download_and_send_media(bot: Bot, chat_id: int, url: str, socNet: str):
    """
    Скачивает медиафайл и отправляет его в Telegram.
    :param bot: Экземпляр бота.
    :param chat_id: ID чата.
    :param url: Ссылка на медиафайл.
    :param socNet: Соцсеть (например, "tiktok", "youtube").
    """
    temp_dir = tempfile.mkdtemp()  # Временная папка для загрузки
    video_id = generate_url_id(url)  # Уникальный ID видео
    filename = os.path.join(temp_dir, f"{video_id}.mp4")  # Уникальное имя файла

    try:
        start_time = time.time()

        # 1️⃣ Получаем список доступных форматов
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url, download=False)
            formats = info.get('formats', [])

        if not formats:
            await bot.send_message(chat_id, "❌ Ошибка: не найдено доступных форматов.")
            return

        # 2️⃣ Выбираем лучший формат
        best_format_id = select_best_format(formats, socNet)
        if not best_format_id:
            await bot.send_message(chat_id, "❌ Ошибка: не найден подходящий формат.")
            return

        logger.info(f"✅ Выбран формат: {best_format_id}")

        # 3️⃣ Скачиваем видео с этим форматом
        real_filename = await download_media(url, best_format_id, filename)

        # 4️⃣ Проверяем размер файла
        if os.path.exists(real_filename):
            file_size = os.path.getsize(real_filename)
            if file_size > MAX_FILE_SIZE:
                await bot.send_message(chat_id, "❌ Файл слишком большой для отправки в Telegram.")
                os.remove(real_filename)
                shutil.rmtree(temp_dir)
                return

            # 5️⃣ Отправляем видео в Telegram
            end_time = time.time()
            elapsed_time = end_time - start_time

            media_file = FSInputFile(real_filename)
            await bot.send_video(chat_id, video=media_file, caption=f"📹 Видео загружено за {elapsed_time:.2f} секунд")
            os.remove(real_filename)  # Удаляем скачанный файл
        else:
            await bot.send_message(chat_id, "❌ Ошибка: файл не найден после загрузки.")

    except Exception as ex:
        logger.error(f"Ошибка при загрузке видео: {ex}")
        await bot.send_message(chat_id, f"❌ Ошибка загрузки: {ex}")

    finally:
        # Удаляем временную папку
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)