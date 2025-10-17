import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from ..Agent.CalendarAgent import CalendarAgent
from ..helpers.Config import get_settings


class TelegramCalendarBot:
    def __init__(self):
        settings = get_settings()
        self.token = settings.TELEGRAM_TOKEN
        self.calendar_agent = CalendarAgent(verbose=False)
        self.application = Application.builder().token(self.token).build()
        self.application.add_handler(MessageHandler(filters.TEXT, self.handle_message))

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_message = update.message.text
        response = self.calendar_agent.chat(user_message)
        await update.message.reply_text(response)

    def start(self):
        print("Starting Telegram Calendar Bot...")
        asyncio.run(self.application.run_polling())

if __name__ == '__main__':
    bot = TelegramCalendarBot()
    bot.start()
        