import asyncio
import os
from config import TELEGRAM_TOKEN as TOKEN

from aiogram import Bot, Dispatcher, types

from handlers import commands, callback 


bot = Bot(TOKEN)

async def main():
    dp = Dispatcher()
    try:
        dp.include_router(commands.router)
     # dp.include_router(callback.router)
   
        print("Bot started")
        await dp.start_polling(bot)
        await bot.session.close()
        
    except Exception as ex:
        print(f"Error: {ex}")
        await bot.session.close()
        
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"Exit")