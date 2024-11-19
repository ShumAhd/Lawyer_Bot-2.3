import re
import json
import logging
import os
from aiogram import Bot, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from aiogram.filters import Command
from config import TOKEN, LAWYER_CHAT_ID

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=TOKEN)
router = Router()

# Путь к файлу хранилища
QUESTIONS_FILE = "questions.json"

# Проверка наличия файла хранилища
if not os.path.exists(QUESTIONS_FILE):
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

# Загрузка вопросов из файла
def load_questions():
    if not os.path.exists(QUESTIONS_FILE):
        return {}
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# Сохранение вопросов в файл
def save_questions(data):
    if not data:
        # Удаляем файл, если данные пустые
        if os.path.exists(QUESTIONS_FILE):
            os.remove(QUESTIONS_FILE)
    else:
        with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

# Хранилище вопросов
user_questions = load_questions()

# FSM для шагов пользователя
class Form(StatesGroup):
    waiting_for_question = State()
    waiting_for_phone = State()

# Приветственное сообщение
WELCOME_MESSAGE = (
    "Здравствуйте! \n\n"
    "Чтобы остановить бота, используйте команду /stop.\n"
    "Чтобы снова начать, используйте команду /start или нажмите кнопку \"Задать новый вопрос юристу\".\n\n"
    "Задайте себе несколько вопросов:\n\n"
    "1. Решение моего вопроса облегчит мне жизнь?\n"
    "2. Я готов воспользоваться ответом юриста?\n"
    "3. Я готов решить данный вопрос окончательно?\n\n"
    "Только если на все вопросы ответ Да!\n\n"
    "Напишите ваш вопрос, и я передам его юристам."
)

# Автоматическое приветствие при добавлении бота
@router.message(lambda message: message.chat.type == "private", Command("start"))
async def start_handler(message: Message, state: FSMContext):
    await message.answer(WELCOME_MESSAGE)
    await state.set_state(Form.waiting_for_question)

# Команда /stop для отмены текущего действия
@router.message(Command("stop"))
async def stop_handler(message: Message, state: FSMContext):
    await state.clear()  # Очистка состояния
    await message.answer("Вы остановили текущий процесс. Чтобы начать заново, используйте команду /start.")

# Обработчик вопроса
@router.message(Form.waiting_for_question)
async def handle_question(message: Message, state: FSMContext):
    question_text = message.text.strip()
    if not question_text:
        await message.answer("Пожалуйста, введите текст вопроса.")
        return

    await state.update_data(question=question_text)
    await message.answer("Введите ваш номер телефона в формате +79241234567.")
    await state.set_state(Form.waiting_for_phone)

# Обработчик телефона
@router.message(Form.waiting_for_phone)
async def handle_phone(message: Message, state: FSMContext):
    if not re.match(r"^\+\d{11}$", message.text):
        await message.answer("Пожалуйста, введите корректный номер телефона.")
        return

    user_data = await state.get_data()
    question = user_data["question"]

    # Отправляем вопрос юристам и сохраняем ID сообщения
    sent_message = await bot.send_message(
        LAWYER_CHAT_ID,
        f"Новый вопрос от @{message.from_user.username or message.from_user.id}:\n\n"
        f"Вопрос: {question}\nТелефон: {message.text}"
    )

    # Сохраняем данные для пользователя
    user_questions[str(sent_message.message_id)] = {
        "user_id": message.from_user.id,
        "question": question,
        "phone": message.text
    }
    save_questions(user_questions)

    # Кнопка "Задать новый вопрос юристу"
    markup = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text='Задать новый вопрос юристу')]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await message.answer(
        "Ваш вопрос отправлен юристам. Спасибо!",
        reply_markup=markup
    )
    await state.clear()

# Обработчик нажатия кнопки "Задать новый вопрос юристу"
@router.message(lambda message: message.text == "Задать новый вопрос юристу")
async def new_question_handler(message: Message, state: FSMContext):
    await message.answer("Напишите ваш новый вопрос:")
    await state.set_state(Form.waiting_for_question)

# Обработчик ответа от юристов
@router.message(lambda message: message.chat.id == LAWYER_CHAT_ID)
async def handle_lawyer_response(message: Message):
    if message.reply_to_message:
        # Ищем данные по ID сообщения, на которое отвечает юрист
        message_id = str(message.reply_to_message.message_id)
        if message_id in user_questions:
            user_data = user_questions[message_id]
            user_id = user_data["user_id"]

            # Отправляем ответ пользователю
            await bot.send_message(
                user_id,
                f"Ответ на ваш вопрос:\n\n{message.text}"
            )

            # Удаляем данные после ответа
            del user_questions[message_id]
            save_questions(user_questions)
        else:
            await message.reply("Не удалось найти пользователя, задавшего этот вопрос.")
    else:
        await message.reply("Пожалуйста, используйте функцию 'Ответить' на сообщение с вопросом.")
