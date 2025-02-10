from aiogram import Router, Bot
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from main import bot

from handlers.function import download_and_send_media
import url_storage as storage

import handlers.function as hf
import url_storage as storage

router = Router()

@router.message(CommandStart())
async def cdm_tart(message: Message):
    await message.answer("Привет, отправь мне ссылку на видео из Тиктока или Ютуба, и я скачаю его для тебя!")
    
@router.message(lambda message: "tiktok.com" in message.text or "youtube.com" in message.text)
async def video_request(message: Message):
    await message.answer("Скачиваю видео...")
    url = message.text.strip()
    url_id = hf.generate_url_id(url)
    storage.url_storage[url_id] = url
    storage.save_url_storage(storage.url_storage)
    storage.url_storage = storage.load_url_storage()
    
    socNet = ""
    if "tiktok.com" in message.text:
        socNet = "tiktok"
    else:
        socNet = "youtube" 
    await download_and_send_media(bot, message.chat.id, url, socNet)
    
    
   
    