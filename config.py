# config.py

import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Токен бота
TOKEN = os.getenv("TOKEN")

# ID чата юристов
LAWYER_CHAT_ID = int(os.getenv("LAWYER_CHAT_ID"))

# Топик для сообщений (если не используется, укажите 0)
TOPIC_ID = int(os.getenv("TOPIC_ID", 0))

# ID основного чата (если совпадает с LAWYER_CHAT_ID, дублируйте значение)
TARGET_CHAT_ID = int(os.getenv("TARGET_CHAT_ID"))
