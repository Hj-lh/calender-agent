from src.helpers.Config import get_settings
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
config = get_settings()
telegram_token = config.TELEGRAM_TOKEN


async def handle_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    user_id = update.message.from_user.id
    print(f"Received message from user {user_id}: {user_message}")
    conversation_history = context.user_data.setdefault('conversation_history', [])
    conversation_history.append({"role": "user", "content": user_message})
    await update.message.reply_text(f"You said: {user_message}")
    if len(conversation_history) > 5:
        conversation_history.pop(0)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data.clear()
    await update.message.reply_text("Hello! I'm a bot with a memory. Let's start a new conversation.")


def main():
    application = ApplicationBuilder().token(telegram_token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_conversation))
    application.run_polling()
if __name__ == '__main__':
    main()