import os
from openai import OpenAI
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# ====== ENV ======
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN not set")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set")

client = OpenAI(api_key=OPENAI_API_KEY)

# ====== LIMITS ======
MAX_INPUT_CHARS = 1000
MAX_OUTPUT_CHARS = 800
MAX_HISTORY = 8

# ====== MEMORY ======
user_memory = {}

SYSTEM_PROMPT = (
    "Ти корисний та короткий асистент. "
    f"Відповідай максимум {MAX_OUTPUT_CHARS} символів. "
    "Не перевищуй це обмеження."
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🤖 Бот онлайн.\n"
        f"Ліміт повідомлення: {MAX_INPUT_CHARS} символів.\n"
        f"Максимальна довжина відповіді: {MAX_OUTPUT_CHARS} символів."
    )

async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_memory[user_id] = []
    await update.message.reply_text("Памʼять очищена 🧹")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text

    # ====== INPUT LIMIT ======
    if len(user_text) > MAX_INPUT_CHARS:
        await update.message.reply_text(
            f"⚠️ Повідомлення занадто довге.\n"
            f"Максимум {MAX_INPUT_CHARS} символів."
        )
        return

    if user_id not in user_memory:
        user_memory[user_id] = [
            {"role": "system", "content": SYSTEM_PROMPT}
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

        # ====== OUTPUT LIMIT ======
        if len(reply) > MAX_OUTPUT_CHARS:
            reply = reply[:MAX_OUTPUT_CHARS] + "..."

        user_memory[user_id].append({"role": "assistant", "content": reply})

        await update.message.reply_text(reply)

    except Exception as e:
        print(e)
        await update.message.reply_text("⚠️ Помилка сервера.")

app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reset", reset))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("🚀 Bot started...")
app.run_polling()
