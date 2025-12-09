import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# تنظیمات
TOKEN = "8410409761:AAFnaVEzATkAcSNH3tFRq6D9OmZDU4FhhwM"
ADMIN_CHANNEL = "@hacking_filltering"
REFERRAL_NEEDED = 4
BOT_USERNAME = "rubika_filterfixbot"

# حالت‌های مکالمه
ENTER_PHONE, ENTER_USERNAME = range(2)

# ذخیره موقت
user_data = {}

# لاگ
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ==================== توابع کمکی ====================
def check_channel_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        member = context.bot.get_chat_member(chat_id=ADMIN_CHANNEL, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def generate_referral_link(user_id: int) -> str:
    return f"https://t.me/{BOT_USERNAME}?start={user_id}"

def validate_phone(phone: str) -> bool:
    phone = phone.strip()
    if phone.startswith("+98") and len(phone) == 13:
        return True
    if phone.startswith("09") and len(phone) == 11:
        return True
    return False

def validate_username(username: str) -> bool:
    username = username.strip()
    return username.startswith("@") and len(username) > 1

# ==================== استارت ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # ردیابی رفرال
    if context.args:
        referrer_id = int(context.args[0])
        if referrer_id in user_data and user_id != referrer_id:
            if check_channel_membership(user_id, context):
                user_data[referrer_id]["referrals"] = user_data[referrer_id].get("referrals", 0) + 1
    
    # ذخیره کاربر جدید
    if user_id not in user_data:
        user_data[user_id] = {
            "referrals": 0,
            "referral_link": generate_referral_link(user_id),
            "accounts": [],
            "phone": "",
            "username": ""
        }
    
    # بررسی عضویت
    if not check_channel_membership(user_id, context):
        keyboard = [
            [InlineKeyboardButton("✅ عضویت در کانال", url=f"https://t.me/hacking_filltering")],
            [InlineKeyboardButton("🔍 بررسی عضویت", callback_data="check_membership")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"سلام {user.first_name}!\nلطفاً در کانال زیر عضو شوید:\n{ADMIN_CHANNEL}",
            reply_markup=reply_markup
        )
        return
    
    # نمایش منوی اصلی
    await show_main_menu(update, context)

async def check_membership_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    if check_channel_membership(user_id, context):
        await query.edit_message_text("✅ عضویت شما تأیید شد!")
        await show_main_menu_from_callback(query, context)
    else:
        await query.answer("⚠️ هنوز در کانال عضو نشدید!", show_alert=True)

# ==================== منو اصلی ====================
async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    referrals = user_data.get(user_id, {}).get("referrals", 0)
    
    keyboard = [
        [InlineKeyboardButton("🛡 رفع فیلتری اکانت", callback_data="unblock_account")],
        [InlineKeyboardButton("📊 حساب من", callback_data="my_account")],
        [InlineKeyboardButton("🔗 لینک دعوت من", callback_data="my_referral")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"👋 سلام {user.first_name}!\n🏆 امتیاز شما: {referrals}/{REFERRAL_NEEDED}"
    
    if hasattr(update, 'message'):
        await update.message.reply_text(text, reply_markup=reply_markup)
    else:
        await update.callback_query.message.reply_text(text, reply_markup=reply_markup)

async def show_main_menu_from_callback(query, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update=Update(update_id=query.id, message=query.message), context=context)

# ==================== رفع فیلتر ====================
async def unblock_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    referrals = user_data.get(user_id, {}).get("referrals", 0)
    
    if referrals < REFERRAL_NEEDED:
        keyboard = [
            [InlineKeyboardButton("🔗 دریافت لینک دعوت", callback_data="my_referral")],
            [InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"⚠️ امتیاز شما کافی نیست!\nامتیاز فعلی: {referrals}/{REFERRAL_NEEDED}\n"
            f"نیاز به {REFERRAL_NEEDED - referrals} نفر دیگر دارید.",
            reply_markup=reply_markup
        )
        return
    
    await query.edit_message_text(
        "✅ امتیاز شما تکمیل شد!\n\n"
        "📱 شماره اکانت را وارد کنید:\n"
        "• با +98 (مثال: +989123456789)\n"
        "• یا با 09 (مثال: 09123456789)"
    )
    return ENTER_PHONE

async def phone_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text
    
    if not validate_phone(phone):
        await update.message.reply_text(
            "❌ شماره نامعتبر!\nفرمت صحیح:\n• +989123456789\n• 09123456789\n\nدوباره وارد کنید:"
        )
        return ENTER_PHONE
    
    user_id = update.effective_user.id
    user_data[user_id]["phone"] = phone
    
    await update.message.reply_text(
        "✅ شماره ثبت شد!\n\n"
        "🌀 آیدی اکانت را وارد کنید:\n"
        "• با @ شروع شود\n• مثال: @username"
    )
    return ENTER_USERNAME

async def username_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text
    user_id = update.effective_user.id
    
    if not validate_username(username):
        await update.message.reply_text(
            "❌ آیدی نامعتبر!\nباید با @ شروع شود.\n\nدوباره وارد کنید:"
        )
        return ENTER_USERNAME
    
    user_data[user_id]["username"] = username
    user_data[user_id]["accounts"].append({
        "phone": user_data[user_id]["phone"],
        "username": username,
        "date": "اکنون"
    })
    
    # کاهش امتیاز
    user_data[user_id]["referrals"] -= REFERRAL_NEEDED
    
    keyboard = [[InlineKeyboardButton("🔙 برگشت به منوی اصلی", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "✅ اکانت شما ثبت شد!\n\n"
        f"📱 شماره: {user_data[user_id]['phone']}\n"
        f"🌀 آیدی: {username}\n\n"
        "⏳ تا 24 ساعت آینده رفع تعلیق خواهد شد.",
        reply_markup=reply_markup
    )
    return ConversationHandler.END

# ==================== حساب من ====================
async def my_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = user_data.get(user_id, {})
    referrals = data.get("referrals", 0)
    
    accounts_text = ""
    for acc in data.get("accounts", []):
        accounts_text += f"📱 {acc['phone']} | 🆔 {acc['username']}\n"
    
    if not accounts_text:
        accounts_text = "هیچ اکانتی ثبت نشده"
    
    text = (
        f"👤 حساب کاربری شما:\n\n"
        f"🏆 امتیاز: {referrals}/{REFERRAL_NEEDED}\n"
        f"📱 شماره: {data.get('phone', 'ثبت نشده')}\n"
        f"🌀 آیدی: {data.get('username', 'ثبت نشده')}\n\n"
        f"📋 اکانت‌ها:\n{accounts_text}\n"
        f"🔗 لینک دعوت: {data.get('referral_link', '')}"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup)

# ==================== لینک دعوت ====================
async def my_referral_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    link = user_data.get(user_id, {}).get("referral_link", "")
    referrals = user_data.get(user_id, {}).get("referrals", 0)
    
    text = (
        f"🔗 لینک دعوت شما:\n\n"
        f"`{link}`\n\n"
        f"🎯 نیاز به {REFERRAL_NEEDED} امتیاز برای هر اکانت\n"
        f"👥 دعوت شده‌ها: {referrals} نفر"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔙 برگشت", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# ==================== برگشت ====================
async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await show_main_menu_from_callback(query, context)

# ==================== اصلی ====================
def main():
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(unblock_account_callback, pattern="^unblock_account$")],
        states={
            ENTER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, phone_handler)],
            ENTER_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, username_handler)],
        },
        fallbacks=[CallbackQueryHandler(main_menu_callback, pattern="^main_menu$")]
    )
    application.add_handler(conv_handler)
    
    application.add_handler(CallbackQueryHandler(check_membership_callback, pattern="^check_membership$"))
    application.add_handler(CallbackQueryHandler(my_account_callback, pattern="^my_account$"))
    application.add_handler(CallbackQueryHandler(my_referral_callback, pattern="^my_referral$"))
    application.add_handler(CallbackQueryHandler(main_menu_callback, pattern="^main_menu$"))
    
    # روی Render از وب‌هوک استفاده می‌کنیم
    port = int(os.environ.get("PORT", 8443))
    webhook_url = os.environ.get("WEBHOOK_URL", "")
    
    if webhook_url:
        application.run_webhook(
            listen="0.0.0.0",
            port=port,
            url_path=TOKEN,
            webhook_url=webhook_url + TOKEN
        )
    else:
        application.run_polling()

if __name__ == "__main__":
    main()
