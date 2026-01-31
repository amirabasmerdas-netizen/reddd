import sqlite3
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, CallbackContext, MessageHandler, filters
import asyncio
import os

# ===========================
# CONFIG
TOKEN = "8284310916:AAFvODpBkQ1rHW4jDkpeNvRoXlIIS-iUEhU"
WEBHOOK_URL = "https://<YOUR-RENDER-URL>.onrender.com/"  # جایگزین با URL رندر شما
DB_FILE = "database.db"
# ===========================

# اتصال به دیتابیس
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

# ساخت جدول‌ها
cursor.execute('''
CREATE TABLE IF NOT EXISTS activities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    time TEXT,
    category TEXT,
    description TEXT,
    done INTEGER DEFAULT 0
)
''')
conn.commit()

# تعریف فعالیت‌ها (می‌توان بعدا اضافه کرد)
activities_schedule = [
    {"time": "07:30", "category": "مدرسه", "description": "کلاس مدرسه 🌟"},
    {"time": "15:30", "category": "تکواندو", "description": "بدنسازی تکواندو 💪"},
    {"time": "09:30", "category": "تکواندو", "description": "فرم تکواندو 🥋"},
    {"time": "15:45", "category": "تکواندو", "description": "مبارزه تکواندو ⚔️"},
    {"time": "14:30", "category": "برنامه‌نویسی", "description": "تمرین برنامه‌نویسی 💻"},
    {"time": "16:30", "category": "ورزش خانگی", "description": "کشش و کاردیو 🏃"},
    {"time": "07:00", "category": "روتین پوستی", "description": "صبحانه و روتین پوستی ☀️"},
    {"time": "16:00", "category": "روتین پوستی", "description": "روتین عصر 🌙"},
    {"time": "21:00", "category": "روتین پوستی", "description": "روتین شب 🌌"}
]

# افزودن فعالیت‌ها به دیتابیس
today_str = datetime.now().strftime("%Y-%m-%d")
for act in activities_schedule:
    cursor.execute("INSERT INTO activities (date, time, category, description) VALUES (?, ?, ?, ?)",
                   (today_str, act["time"], act["category"], act["description"]))
conn.commit()


# ===========================
# COMMAND HANDLERS
# ===========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! من ربات کنترل روتین 🌟 هستم.\nمن بهت یادآوری می‌کنم و فعالیت‌ها رو مدیریت می‌کنم!"
    )

async def list_activities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT id, time, description, done FROM activities WHERE date=?", (today,))
    rows = cursor.fetchall()
    if not rows:
        await update.message.reply_text("امروز فعالیتی ثبت نشده 😅")
        return
    message = "فعالیت‌های امروز 📅:\n"
    for r in rows:
        status = "✅" if r[3] else "❌"
        message += f"{r[1]} - {r[2]} {status}\n"
    await update.message.reply_text(message)


# ===========================
# CALLBACK HANDLER
# ===========================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("done_"):
        act_id = int(data.split("_")[1])
        cursor.execute("UPDATE activities SET done=1 WHERE id=?", (act_id,))
        conn.commit()
        await query.edit_message_text(text=f"فعالیت ثبت شد ✅")
        

# ===========================
# SCHEDULER
# ===========================

async def scheduler(app):
    while True:
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M")
        cursor.execute("SELECT id, description FROM activities WHERE date=? AND time=? AND done=0", (today, current_time))
        rows = cursor.fetchall()
        for r in rows:
            act_id = r[0]
            description = r[1]
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("انجام شد ✅", callback_data=f"done_{act_id}")]
            ])
            await app.bot.send_message(chat_id="@YOUR_CHANNEL_OR_USERID", text=f"⏰ وقت انجام فعالیت:\n{description}", reply_markup=keyboard)
        await asyncio.sleep(60)


# ===========================
# MAIN
# ===========================

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("فعالیت‌ها", list_activities))
    app.add_handler(CallbackQueryHandler(button))
    
    # راه اندازی scheduler به صورت async
    loop = asyncio.get_event_loop()
    loop.create_task(scheduler(app))
    
    # وب هوک برای Render
    app.run_webhook(listen="0.0.0.0", port=int(os.environ.get("PORT", 8443)), url_path=TOKEN, webhook_url=WEBHOOK_URL+TOKEN)
