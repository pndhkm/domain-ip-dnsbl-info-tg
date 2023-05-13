import os,responses,logging, re
from check_domain import domain
from check_ip import ip, is_public_ip, bls_list
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler,Updater, CommandHandler, CallbackQueryHandler,Filters
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

load_dotenv()
TOKEN =  os.getenv('TOKEN')
bl_servers = os.getenv('BLSEVER').split(',')
admin_chat_id = int(os.getenv('ADMIN_CHAT_ID'))

def check_user(userid):
    with open('user.txt', 'r') as f:
        users = f.read()
    if str(userid) not in users:
        return False
    else:
        return True
        

def register(update, context):
    try:
        logging.info("User %s register ...", update.message.from_user.username)
        with open('user.txt', 'r') as f:
            users = f.read()
        id_message = update.message.chat.id
        if str(id_message) not in users:
            context.bot.send_message(chat_id=update.message.chat_id, text="Oke, aku udah teruskan ke admin\nmohon ditunggu ya")
            global id_register
            id_register = update.message.chat.id
            keyboard = [
                [
                    InlineKeyboardButton("Accept", callback_data='accept'),
                    InlineKeyboardButton("Decline", callback_data='decline'),
                ]
            ]
            prmt = InlineKeyboardMarkup(keyboard)
            context.bot.send_message(chat_id=admin_chat_id, text="id: " + str(update.message.chat_id) + "\nusername: @" + update.message.from_user.username + " \nmau daftar", reply_markup=prmt)
        else:
            context.bot.send_message(chat_id=update.message.chat_id, text="Akun kamu sudah terdaftar ya\n\nlihat panduan penggunaan: /help")
    except Exception as e:
        logging.error(update.message.from_user.username + ' register: ' + str(e))
        

def help(update, context):
    try:
        id_message = update.message.chat.id
        if check_user(id_message) == True:
            context.bot.send_message(chat_id=update.message.chat_id, text="Untuk periksa domain atau alamat IP silahkan pilih menu <b>periksa</b> atau tekan: /check", parse_mode='html')
        else:
            context.bot.send_message(chat_id=update.message.chat_id, text="Akun kamu belum terdaftar\nkamu belum bisa menggunakan fitur ini.\n\n<b>Cara Mendaftar</b>\n1. Tekan: /register \n2. Tunggu hingga admin/bot menghubungimu\n3. Setelah itu silahkan lihat panduan: /help", parse_mode='html')
    except Exception as e:
        logging.error('Help: ' + str(e))
        
def blserver_lists(update, context):
    try:
        id_message = update.message.chat.id
        if check_user(id_message) == False:
            context.bot.send_message(chat_id=update.message.chat_id, text="Maaf,aku gakenal sama kamu")
            context.bot.send_message(chat_id=update.message.chat_id, text="lihat panduan : /help")
            return
        message = bls_list()
        context.bot.send_message(chat_id=update.message.chat_id, text="<b>Server Blacklists:</b>" + message, parse_mode='html')
    except Exception as e:
        logging.error('Show blacklist servers: ' + str(e))

def handle_message(update, context):
    try:
        content = update.message.text
        id_message = update.message.chat.id
        if check_user(id_message) == False:
            context.bot.send_message(chat_id=update.message.chat_id, text="Maaf,aku gakenal sama kamu")
            context.bot.send_message(chat_id=update.message.chat_id, text="lihat panduan : /help")
            return
        
        if context.user_data.get('state') == 'WAITING_FOR_DOMAIN':
            # Hapus state 'WAITING_FOR_DOMAIN' dari user data
            del context.user_data['state']
            message_id = context.bot.send_message(chat_id=update.message.chat_id, text="Baik, mohon ditunggu").message_id
            message = domain(content) 
            context.bot.delete_message(chat_id=update.message.chat_id, message_id=message_id)
            recheck(update, message, 'redomain') 
            context.user_data['domain'] = content 
        
        elif context.user_data.get('state') == 'WAITING_FOR_IP':
            del context.user_data['state']
            if not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', content):
                message = "Alamat IP tidak dikenal, gunakan format alamat IP. Contoh:\n<code>8.8.8.8</code>"
            elif not is_public_ip(content):
                message = "IP " + content + " bukan publik IP"
                message_id = context.bot.send_message(chat_id=update.message.chat_id, text="Baik, mohon ditunggu").message_id
            else:
                message_id = context.bot.send_message(chat_id=update.message.chat_id, text="Baik, mohon ditunggu").message_id
                message = ip(content)  
                context.bot.delete_message(chat_id=update.message.chat_id, message_id=message_id)
                
            recheck(update, message, 'reip')
            context.user_data['ip'] = content           
            
        else:
            text = str(update.message.text).lower()
            logging.info(f'User ({update.message.chat.id}) says: {text}')
            response = responses.get_response(text)
            update.message.reply_text(response)
            
    except Exception as e:
        logging.error(f'Handle messages: {update} ' + str(e))
        

def check(update, context):
    try:
        id_message = update.message.chat.id
        if check_user(id_message) == False:
            context.bot.send_message(chat_id=update.message.chat_id, text="Maaf,aku gakenal sama kamu")
            context.bot.send_message(chat_id=update.message.chat_id, text="lihat panduan : /help")
            return
        else:
            keyboard = [
                [
                    InlineKeyboardButton("Periksa Domain", callback_data='ckdomain'),
                ],
                [
                    InlineKeyboardButton("Periksa Alamat IP", callback_data='ckip'),
                ],
            ]

            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text("Menu", reply_markup=reply_markup)
    except Exception as e:
        logging.error(f'Check {id_message} ' + str(e))

def recheck(update, context, dynamic):
    try:
        keyboard = [
            [
                InlineKeyboardButton("Periksa Ulang", callback_data=dynamic),
            ],
            [
                InlineKeyboardButton("Periksa Yang Lain »", callback_data='backtomenu'),
            ],
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(context, reply_markup=reply_markup, parse_mode='HTML')
        
    except Exception as e:
        logging.error('Recheck: ' + str(e))

def button(update, context):
    try:
        query = update.callback_query
        query.answer()
        choice = query.data
        chat_id = query.message.chat_id
        message_id = query.message.message_id

        if choice == 'accept':
            with open('user.txt', 'a') as f:
                f.write(f"\n{id_register}")
            context.bot.send_message(chat_id=id_register, text="Yeay, kamu berhasil terdaftar\nsilahkan baca panduan untuk menggunakan bot ini: /help")
        elif choice == 'decline':
            context.bot.send_message(chat_id=id_register, text="Access Denied")
        elif choice == 'ckdomain':
            context.bot.send_message(chat_id=query.message.chat_id, text='Silahkan masukan nama domain')
            context.user_data['state'] = 'WAITING_FOR_DOMAIN'
        elif choice == 'ckip':
            context.bot.send_message(chat_id=query.message.chat_id, text='Silahkan masukan alamat IP')
            context.user_data['state'] = 'WAITING_FOR_IP'
        elif choice == 'redomain':
            try:    
                message = domain(context.user_data['domain'])
                recheck(query, message, 'redomain')
            except:
                context.bot.send_message(chat_id=query.message.chat_id, text='Mohon maaf aku gak memhami permintaan itu, silahkan baca panduan /help')
        elif choice == 'reip':
            try:
                message = ip(context.user_data['ip'])
                recheck(query, message, 'reip')
            except:
                context.bot.send_message(chat_id=query.message.chat_id, text='Mohon maaf aku gak memhami permintaan itu, silahkan baca panduan /help')
        elif choice == 'backtomenu':
            keyboard = [
                [
                    InlineKeyboardButton("Periksa Domain", callback_data='ckdomain'),
                ],
                [
                    InlineKeyboardButton("Periksa Alamat IP", callback_data='ckip'),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            context.bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=reply_markup)
            
        else:
            context.bot.send_message(chat_id=query.message.chat_id, text='Mohon maaf aku gak memhami permintaan itu, silahkan baca panduan /help')

    except Exception as e:
        logging.error(f'Button ' + str(e))

def blserver_tests(update, context):
    try:
        id_message = update.message.chat.id
        if check_user(id_message) == False:
            context.bot.send_message(chat_id=update.message.chat_id, text="Maaf,aku gakenal sama kamu")
            context.bot.send_message(chat_id=update.message.chat_id, text="lihat panduan : /help")
            return
        
        message_id = context.bot.send_message(chat_id=update.message.chat_id, text="Baik, mohon ditunggu").message_id
        message = bls_test_conn()
        context.bot.delete_message(chat_id=update.message.chat_id, message_id=message_id)
        context.bot.send_message(chat_id=update.message.chat_id, text=message, parse_mode='html')
    except Exception as e:
        logging.error(f'server blstatus ' + str(e))

def blinfo(update, context):
    try:
        id_message = update.message.chat.id
        if check_user(id_message) == False:
            context.bot.send_message(chat_id=update.message.chat_id, text="Maaf,aku gakenal sama kamu")
            context.bot.send_message(chat_id=update.message.chat_id, text="lihat panduan : /help")
            return
        context.bot.send_message(chat_id=update.message.chat_id, text="Lihat daftar server blacklist: /blserver_lists")
    except Exception as e:
        logging.error(f'blinfo ' + str(e))

updater = Updater(token=TOKEN, use_context=True)
dp = updater.dispatcher
dp.add_handler(CommandHandler('help', help))
dp.add_handler(CommandHandler('register', register))
dp.add_handler(CommandHandler('check', check))
dp.add_handler(CommandHandler('blinfo', blinfo))
dp.add_handler(CommandHandler('blserver_lists', blserver_lists))
dp.add_handler(MessageHandler(Filters.text, handle_message))
dp.add_handler(CallbackQueryHandler(button))    

logging.info("Listening...")
updater.start_polling(1.0)
updater.idle()