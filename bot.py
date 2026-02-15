import os
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# ====== ЧИТАННЯ token.env БЕЗ dotenv ======

def load_env_file(filename):
    with open(filename) as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

load_env_file("token.env")

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN не знайдено в token.env")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY не знайдено в token.env")

# ====== OpenAI ======
client = OpenAI(api_key=OPENAI_API_KEY)

# ====== Памʼять ======
user_memory = {}
MAX_HISTORY = 10

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привіт 👋 Я AI бот з памʼяттю. Напиши щось.")

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_memory[user_id] = []
    await update.message.reply_text("Памʼять очищена 🧹")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    if user_id not in user_memory:
        user_memory[user_id] = [
            {"role": "system", "content": "Ти корисний асистент."}
        ]

    user_memory[user_id].append({"role": "user", "content": user_text})

    if len(user_memory[user_id]) > MAX_HISTORY:
        user_memory[user_id] = [user_memory[user_id][0]] + user_memory[user_id][-MAX_HISTORY:]

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=user_memory[user_id],
            max_tokens=300
        )

        reply = response.choices[0].message.content
        user_memory[user_id].append({"role": "assistant", "content": reply})

        await update.message.reply_text(reply)

    except Exception as e:
        await update.message.reply_text("Сталася помилка.")
        print(e)

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("Бот запущений 🚀")
app.run_polling()
