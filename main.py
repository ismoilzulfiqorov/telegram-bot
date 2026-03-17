import telebot
from telebot import types
import time

# --- SOZLAMALAR ---
TOKEN = '8547617381:AAEirNOzZhgB6rI-orv7on0IrJ6pZIRZ8YI'
ADMIN_ID = 6704751996

bot = telebot.TeleBot(TOKEN)

# Foydalanuvchi ma'lumotlarini vaqtincha saqlash
user_data = {}

@bot.message_handler(commands=['start', 'yangi'])
def start(message):
    user_id = message.from_user.id
    user_data[user_id] = {}
    bot.send_message(message.chat.id, "Assalomu alaykum! Murojaat yo'llash uchun ism va familiyangizni kiriting:")
    bot.register_next_step_handler(message, get_name)

def get_name(message):
    user_id = message.from_user.id
    user_data[user_id]['ism'] = message.text
    bot.send_message(message.chat.id, "Sinfingizni kiriting (masalan: 9-A):")
    bot.register_next_step_handler(message, get_class)

def get_class(message):
    user_id = message.from_user.id
    user_data[user_id]['sinf'] = message.text
    bot.send_message(message.chat.id, "Murojaatingizni batafsil yozib qoldiring:")
    bot.register_next_step_handler(message, get_text)

def get_text(message):
    try:
        user_id = message.from_user.id
        if user_id not in user_data:
            bot.send_message(message.chat.id, "Xatolik yuz berdi. Iltimos, /start bosing.")
            return

        ism = user_data[user_id]['ism']
        sinf = user_data[user_id]['sinf']
        matn = message.text
        user_data[user_id]['murojaat_matni'] = matn  # Store the request text
        user_data[user_id]['murojaat_message_id'] = message.message_id # Store student's message_id for reply

        murojaat_text = (f"🔔 **Yangi murojaat!**\n\n"
                         f"👤 **Kimdan:** {ism}\n"
                         f"🏫 **Sinf:** {sinf}\n"
                         f"📝 **Murojaat:** {matn}\n"
                         f"🆔 **User ID:** `{user_id}`")

        # Inline tugmalar yaratish
        markup_admin = types.InlineKeyboardMarkup()
        btn_resolve = types.InlineKeyboardButton("✅ Hal qilindi", callback_data=f"resolve_{user_id}")
        btn_reject = types.InlineKeyboardButton("❌ Rad etildi", callback_data=f"reject_{user_id}")
        markup_admin.add(btn_resolve, btn_reject)

        # Adminga yuborish (tugmalar bilan birga)
        bot.send_message(ADMIN_ID, murojaat_text, parse_mode="Markdown", reply_markup=markup_admin)

        # Foydalanuvchiga tasdiq
        markup_user = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup_user.add(types.KeyboardButton("/yangi"))
        bot.send_message(message.chat.id, "✅ Murojaatingiz qabul qilindi! Ma'muriyat ko'rib chiqqandan so'ng sizga xabar beriladi.", reply_markup=markup_user)
    except Exception as e:
        bot.send_message(message.chat.id, f"Xatolik yuz berdi. Qaytadan urinib ko'ring: {e}")

# Admin uchun xabar yuborish (eski usul, tugmalar qo'shilganidan keyin kamroq ishlatiladi)
@bot.message_handler(commands=['hal_etildi'])
def resolve_command(message):
    if message.from_user.id == ADMIN_ID:
        try:
            parts = message.text.split(maxsplit=2) # Split into max 2 parts: command, target_id, rest_of_message
            if len(parts) < 2:
                bot.send_message(ADMIN_ID, "⚠️ Xato! Foydalanish: `/hal_etildi USER_ID [javob matni]`", parse_mode="Markdown")
                return

            target_id = int(parts[1])

            admin_custom_message = ""
            if len(parts) > 2:
                admin_custom_message = parts[2].strip()

            resolved_request_text = ""
            student_message_id = None
            if target_id in user_data:
                resolved_request_text = user_data[target_id].get('murojaat_matni', '')
                student_message_id = user_data[target_id].get('murojaat_message_id')

            student_message_parts = []
            if admin_custom_message:
                student_message_parts.append(f"**Ma'muriyatdan javob:** {admin_custom_message}")
            else:
                student_message_parts.append("🎉 **Xushxabar!** Murojaatingiz maktab ma'muriyati tomonidan ko'rib chiqildi va hal etildi.")

            if resolved_request_text:
                student_message_parts.append(f"Sizning murojaatingiz: \"_{resolved_request_text}_\"")

            student_message = "\n\n".join(student_message_parts)

            # Replying to the student's original message if message_id is available
            if student_message_id:
                bot.send_message(target_id, student_message, parse_mode="Markdown", reply_to_message_id=student_message_id)
            else:
                bot.send_message(target_id, student_message, parse_mode="Markdown")

            bot.send_message(ADMIN_ID, f"✅ ID {target_id} ga javob yuborildi.")
        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ Yuborishda xatolik: {e}")

# Inline tugma bosilganda ishlash uchun handler
@bot.callback_query_handler(func=lambda call: call.data.startswith(('resolve_', 'reject_')))
def callback_inline(call):
    if call.from_user.id == ADMIN_ID:
        try:
            action, target_user_id_str = call.data.split('_', 1)
            target_user_id = int(target_user_id_str)

            resolved_request_text = ""
            student_message_id = None
            if target_user_id in user_data:
                resolved_request_text = user_data[target_user_id].get('murojaat_matni', '')
                student_message_id = user_data[target_user_id].get('murojaat_message_id')

            student_response = ""
            admin_update_text = ""

            if action == 'resolve':
                student_response = "🎉 **Xushxabar!** Murojaatingiz maktab ma'muriyati tomonidan ko'rib chiqildi va **hal etildi.**"
                admin_update_text = "✅ Murojaat **hal etildi.**"
            elif action == 'reject':
                student_response = "😔 **Afsuski,** sizning murojaatingiz maktab ma'muriyati tomonidan ko'rib chiqildi va **rad etildi.**"
                admin_update_text = "❌ Murojaat **rad etildi.**"

            if resolved_request_text:
                student_response += f"\n\nSizning murojaatingiz: \"_{resolved_request_text}_\""

            # Foydalanuvchiga javob yuborish (agar message_id mavjud bo'lsa, unga reply qilinadi)
            if student_message_id:
                bot.send_message(target_user_id, student_response, parse_mode="Markdown", reply_to_message_id=student_message_id)
            else:
                bot.send_message(target_user_id, student_response, parse_mode="Markdown")

            # Adminning xabarini yangilash (tugmalarni olib tashlab)
            original_admin_text = call.message.text
            new_admin_text = f"{original_admin_text}\n\n**Holat:** {admin_update_text} (Admin: {call.from_user.first_name})"
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=new_admin_text,
                reply_markup=None, # Tugmalarni olib tashlash
                parse_mode="Markdown"
            )
            bot.answer_callback_query(call.id, text=f"Murojaat {admin_update_text.lower().replace('murojaat ', '')}")

        except Exception as e:
            bot.send_message(ADMIN_ID, f"❌ Amalni bajarishda xatolik: {e}")
            bot.answer_callback_query(call.id, text="Xatolik yuz berdi!")

# --- BOTNI ISHGA TUSHIRISH (TIMEOUTDAN HIMOYALANGAN) ---
if __name__ == '__main__':
    print("Bot ishga tushmoqda...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=60)
        except Exception as e:
            print(f"Xatolik yuz berdi, 5 soniyadan so'ng qayta ulanadi: {e}")
            time.sleep(5)
