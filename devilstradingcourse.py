import telebot
import time
import os
import json

# Токен вашего бота
BOT_TOKEN = "5298337111:AAFFcRfdJy96pkB6G7_aJKM6duC4qyPFVo8"
bot = telebot.TeleBot(BOT_TOKEN)

# Папка для хранения загруженных файлов
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Файл для хранения очереди видео
QUEUE_FILE = "queue.json"
if not os.path.exists(QUEUE_FILE):
    with open(QUEUE_FILE, "w") as file:
        json.dump([], file)

# Файл для хранения пользователей
USERS_FILE = "users.json"
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as file:
        json.dump([], file)

ADMIN_USERNAME = "Nikita_Komendant"  # Ваш Telegram username без @

# Загрузка данных из файлов
def load_data(file_path):
    with open(file_path, "r") as file:
        return json.load(file)

# Сохранение данных в файл
def save_data(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file)

# Добавление файла в очередь
def add_to_queue(file_path, caption):
    queue = load_data(QUEUE_FILE)
    queue.append({"file_path": file_path, "caption": caption})
    save_data(QUEUE_FILE, queue)

# Удаление первого элемента из очереди
def remove_from_queue():
    queue = load_data(QUEUE_FILE)
    if queue:
        queue.pop(0)
        save_data(QUEUE_FILE, queue)

# Добавление пользователя в список
def add_user(user_id):
    users = load_data(USERS_FILE)
    if user_id not in users:
        users.append(user_id)
        save_data(USERS_FILE, users)

# Команда /start
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.chat.id
    add_user(user_id)
    bot.send_message(
        user_id,
        "Привет! Вы будете получать одно видео каждый день. Ожидайте обновлений!"
    )

# Обработка загрузки видео и файлов от администратора
@bot.message_handler(content_types=["video", "document"])
def handle_files(message):
    if message.from_user.username != ADMIN_USERNAME:
        bot.send_message(message.chat.id, "Только администратор может добавлять видео в очередь.")
        return

    try:
        if message.video:
            file_id = message.video.file_id
            file_info = bot.get_file(file_id)
            file_path = file_info.file_path
            local_path = os.path.join(UPLOAD_FOLDER, f"video_{file_id}.mp4")
        elif message.document:
            file_id = message.document.file_id
            file_info = bot.get_file(file_id)
            file_path = file_info.file_path
            local_path = os.path.join(UPLOAD_FOLDER, message.document.file_name)

        # Скачивание файла
        downloaded_file = bot.download_file(file_path)
        with open(local_path, "wb") as new_file:
            new_file.write(downloaded_file)

        # Добавление файла в очередь
        caption = message.caption if message.caption else ""
        add_to_queue(local_path, caption)

        bot.send_message(message.chat.id, "Файл добавлен в очередь для рассылки!")
    except Exception as e:
        bot.send_message(message.chat.id, f"Произошла ошибка: {e}")

# Автоматическая рассылка видео
def auto_post():
    while True:
        queue = load_data(QUEUE_FILE)
        if queue:
            item = queue[0]
            users = load_data(USERS_FILE)

            for user_id in users:
                try:
                    with open(item["file_path"], "rb") as file:
                        if item["file_path"].endswith(".mp4"):
                            bot.send_video(user_id, file, caption=item["caption"])
                        else:
                            bot.send_document(user_id, file, caption=item["caption"])
                except Exception as e:
                    print(f"Ошибка отправки для пользователя {user_id}: {e}")

            print(f"Отправлено: {item['file_path']}")
            remove_from_queue()

        time.sleep(86400)  # Отправка раз в день

# Запуск бота
if __name__ == "__main__":
    import threading

    # Запускаем авто-постинг в отдельном потоке
    threading.Thread(target=auto_post, daemon=True).start()

    # Запускаем бота
    bot.polling(none_stop=True)
