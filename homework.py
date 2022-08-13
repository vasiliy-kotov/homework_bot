"""Главный файл приложения бота."""
import logging
import os
import sys
import time
from logging.handlers import RotatingFileHandler

import requests
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)  # Решил потренироваться в
# создании отдельного логгера
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s - '
                              + '%(funcName)s')

# Хэндлер для управления лог-файлами
handler = RotatingFileHandler(
    'homework.log',
    maxBytes=50000000,
    backupCount=2,
)
handler.setFormatter(formatter)
logger.addHandler(handler)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Ниже представлены переменные для сохранения состояния ошибок и не
# отправки их в Телеграм при их повторении
get_api_answer_message_status_code_not_200 = ''
gaamscn2 = get_api_answer_message_status_code_not_200
get_api_answer_message_connection_exception = ''
gaamce = get_api_answer_message_connection_exception
get_api_answer_message_exception = ''
gaame = get_api_answer_message_exception


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат.

    Чат определяется переменной окружения TELEGRAM_CHAT_ID. Принимает
    на вход два параметра:
    - экземпляр класса Bot,
    - строку с текстом сообщения.
    """
    try:
        TELEGRAM_CHAT_ID
    except Exception as error:
        logger.error(f'У бота нет токена и ид чата. Ошибка - {error}.')
        logger.critical(f'У бота нет токена и ид чата. Ошибка - {error}.')
    else:
        try:
            bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message,
            )
            logger.info(f'В чат телеграм отправлено сообщение - "{message}".')
        except Exception as error:
            logger.error(
                f'Cбой при отправке сообщения в Telegram. Ошибка - {error}.'
            )


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса.

    В качестве параметра функция получает временную метку.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])
    except Exception as error:
        logger.critical(
            f'Не удалось создать экземпляр bot. Ошибка - {error}.'
        )
    else:
        bot = Bot(token=TELEGRAM_TOKEN)
    global gaamscn2
    global gaamce
    global gaame
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        # В случае успешного запроса должна вернуть ответ API,
        # преобразовав его из формата JSON к типам данных Python.
    except Exception as error:
        message_exception = f'Ошибка Exception при запросе к API: {error}'
        if message_exception != gaame:
            logger.error(message_exception)
            send_message(bot, message_exception)
            gaame = message_exception
        else:
            logger.error(message_exception)
    else:
        pass
    if response.status_code != 200:
        status_code = response.status_code
        message_status_code_not_200 = (
            f'Ошибка запроса к API. Код не равен 200. Код -{status_code}.'
        )
        if message_status_code_not_200 != gaamscn2:
            logger.error(message_status_code_not_200)
            send_message(bot, message_status_code_not_200)
            gaamscn2 = message_status_code_not_200
        else:
            logger.error(message_status_code_not_200)
        raise Exception(message_status_code_not_200)
    elif response.status_code == 500:
        raise Exception(f'Ошибка запроса к API. Код {response.status_code}.')
    else:
        return response.json()


def check_response(response):
    """Проверяет ответ API на корректность.

    Получает ответ API, приведенный к типам данных Python.
    """
    try:
        all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])
    except Exception as error:
        logger.critical(
            f'Не удалось создать экземпляр bot. Ошибка - {error}.'
        )
    else:
        bot = Bot(token=TELEGRAM_TOKEN)
    # Если ответ API соответствует ожиданиям, то функция должна вернуть
    # список домашних работ (он может быть и пустым), доступный в
    # ответе API по ключу 'homeworks'.
    homeworks = response['homeworks']  # достаём list работ
    homework = homeworks[0]  # достаём dict одной работы из list
    current_date = response['current_date']
    if not isinstance(response, dict):
        raise TypeError('Ответ АПИ не словарь.')
    if current_date is None:
        message = 'В ответе АПИ отсутствует ключ current_date.'
        logger.error(message)
        send_message(bot, message)
        raise KeyError(message)
    if homeworks is None:
        message = 'В ответе АПИ отсутствует ключ homeworks.'
        logger.error(message)
        send_message(bot, message)
        raise KeyError(message)
    return homework


def parse_status(homework):
    """
    Парсит данные о домашних работах.

    Извлекает из информации о конкретной домашней работе статус этой
    работы. В качестве параметра функция получает только один элемент
    из списка домашних работ.
    """
    try:
        all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])
    except Exception as error:
        logger.critical(
            f'Не удалось создать экземпляр bot. Ошибка - {error}.'
        )
    else:
        bot = Bot(token=TELEGRAM_TOKEN)
    if 'homework_name' not in homework:
        message = 'В объекте homework нет ключа homework_name.'
        logger.error(message)
        send_message(bot, message)
        raise KeyError(message)
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status in HOMEWORK_STATUSES:
        verdict = HOMEWORK_STATUSES[homework_status]
        # В случае успеха, функция возвращает подготовленную для
        # отправки в Telegram строку, содержащую один из вердиктов
        # словаря HOMEWORK_STATUSES.
        return (
            f'Изменился статус проверки работы "{homework_name}". {verdict}'
        )
    else:
        message = (
            'Переменная homework_status со значение '
            + f'"{homework_status}" не соответствует ожидаемым.'
        )
        logger.error(message)
        send_message(bot, message)
        raise NameError(message)


def check_tokens():
    """Проверяет доступность переменных окружения для работы программы.

    Окружения:
    - PRACTICUM_TOKEN,
    - TELEGRAM_TOKEN,
    - TELEGRAM_CHAT_ID.
    Если отсутствует хотя бы одна переменная окружения — функция
    должна вернуть False, иначе — True.
    """
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main():
    """Основная логика работы бота."""
    try:
        all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])
    except Exception as error:
        logger.critical(
            f'Не удалось создать экземпляр bot. Ошибка - {error}.'
        )
    else:
        bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = 1646906700  # Временная отметка начала моего
    # обучения на курсе
    current_homework = {}
    logger.info(f'current_homework {current_homework}')
    while True:
        try:
            check_tokens()
            # Сделать запрос к API.
            response = get_api_answer(current_timestamp)
            # Проверить ответ.
            homework = check_response(response)
            if homework != current_homework:
                # Если есть обновления — получить статус работы из
                # обновления и отправить сообщение в Telegram.
                message = parse_status(homework)
                send_message(bot, message)
                current_homework = homework
            else:
                message = 'Статус работы прежний.'
                logger.debug(message)
                send_message(bot, message)
            # Подождать некоторое время и сделать новый запрос.
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы при запуске функции: {error}'
            logger.error(message)
            send_message(bot, message)
            time.sleep(RETRY_TIME)
        else:
            message = 'Проверяем статус работы'
            send_message(bot, message)


if __name__ == '__main__':
    main()
