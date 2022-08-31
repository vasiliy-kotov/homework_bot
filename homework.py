"""Главный файл приложения бота."""
from ast import expr_context
import logging
import os
import string
import requests
import sys
import time

from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from http import HTTPStatus
from mycustomerror import MyCustomError
from telegram import Bot

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 6  # 00
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)

# Ниже представлены переменные для сохранения состояния ошибок и не
# отправки их в Телеграм при их повторении
get_api_answer_message_status_code_not_200 = ''
gaamscn2 = get_api_answer_message_status_code_not_200
# get_api_answer_message_connection_exception = ''
# gaamce = get_api_answer_message_connection_exception
# get_api_answer_message_exception = ''
# gaame = get_api_answer_message_exception


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат.

    Чат определяется переменной окружения TELEGRAM_CHAT_ID. Принимает
    на вход два параметра:
    - экземпляр класса Bot,
    - строку с текстом сообщения.
    """
    # try:
    # ## добавить лог на то, что бот начал отправку сообщения
    logger.info(f'Инициализируем объект bot - {bot}.')
    # logger.error(f'Ошибка инициализации объекта bot - {bot}.')
    if not bot:
        message = f'Ошибка инициализации объекта bot - {bot}.'
        logger.error(message, exc_info=True)
        raise MyCustomError(message)
    else:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
        logger.info(f'В чат отправлено сообщение - "{message}".')
        # logger.error(f'Ошибка отправки сообщения в чат - "{message}".')


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса.

    В качестве параметра функция получает временную метку.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    bot = Bot(token=TELEGRAM_TOKEN)
    global gaamscn2
    # gaamscn2 = ''
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        status_code = response.status_code
        message_status_code_not_200 = (
            f'Ошибка запроса к API. Код не равен 200. Код - {status_code}.'
        )
        if message_status_code_not_200 != gaamscn2:
            logger.error(message_status_code_not_200)
            send_message(bot, message_status_code_not_200)
            gaamscn2 = message_status_code_not_200
        else:
            logger.error(message_status_code_not_200)
            raise MyCustomError(message_status_code_not_200)
    # elif response.status_code == 500:
    #     raise Exception(f'Ошибка запроса к API. Код {response.status_code}.')
    else:
        # В случае успешного запроса должна вернуть ответ API,
        # преобразовав его из формата JSON к типам данных Python.
        response = response.json()
        return response


def check_response(response):
    """Проверяет ответ API на корректность.

    Получает ответ API, приведенный к типам данных Python.
    """
    # bot = Bot(token=TELEGRAM_TOKEN)
    # Если ответ API соответствует ожиданиям, то функция должна вернуть
    # список домашних работ (он может быть и пустым), доступный в
    # ответе API по ключу 'homeworks'.
    # homework = homeworks[0]  # достаём dict одной работы из list
    if not isinstance(response, dict):
        message = 'Ответ АПИ (response) не словарь.'
        logger.error(message)
        raise TypeError(message)
        # raise MyCustomError(message)
    else:
        # homeworks = response['homeworks']  # достаём list работ
        # current_date = response['current_date']
        logger.info(f'response из check_response - {response}.')
        if 'homeworks' and 'current_date' not in response:
            message = ('В ответе АПИ отсутствует список работ и текущая дата '
                       + '(ключи homeworks и current_date).')
            logger.error(message)
            # send_message(bot, message)
            # raise KeyError(message)
            raise MyCustomError(message)
        # if 'current_date' not in response:
        #     message = 'В ответе АПИ отсутствует ключ current_date.'
        #     logger.error(message)
        #     send_message(bot, message)
        #     raise KeyError(message)
        # return homework
        else:
            homeworks = response['homeworks']
            if not isinstance(homeworks, list):
                message = 'Список работ (homeworkS) не list.'
                logger.error(message)
                # send_message(bot, message)
                raise TypeError(message)
                # raise MyCustomError(message)
            else:
                # logger.info(f'homeworks из check_response - {homeworks}.')
                # return homeworks
                if homeworks is None:
                    message = 'Список работ (homeworkS) пуст.'
                    logger.error(message)
                    # send_message(bot, message)
                    # raise ValueError(message)
                    raise MyCustomError(message)
                else:
                    homework = homeworks[0]
                    # Возвращает dict с данными одной работы
                    if not isinstance(homework, dict):
                        message = 'Содержимое работы (homeworK) не dict.'
                        logger.error(message)
                        raise TypeError(message)
                        # raise MyCustomError(message)
                    else:
                        return homework


def parse_status(homework):
# def parse_status(homeworks):
    """
    Парсит данные о домашних работах.

    Извлекает из информации о конкретной домашней работе статус этой
    работы. В качестве параметра функция получает только один элемент
    из списка домашних работ.
    """
    logger.info(f'homework из parse_status - {homework}.')
    logger.info(f'тип homework из parse_status - {type(homework)}.')
    # if not isinstance(homework, dict):
    #     message = 'Содержимое работы (homeworK) не dict.'
    #     logger.error(message)
    #     raise TypeError(message)
    # else:
    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
        if 'homework_name' and 'status' not in homework:
            message = (
                'В содержимом работы (homework) нет имени и '
                + 'статуса работы (ключи homework_name '
                + 'status).'
            )
            logger.error(message)
            raise KeyError(message)
        else:
            # # homework_name = homework['homework_name']
            # # homework_status = homework['status']
            # # if not isinstance((homework_name and homework_status), str):
            # if not isinstance((homework['homework_name'] and homework['status']), str):
            #     message = (
            #         'По ключам homework_name ('
            #         + f'{homework_name}) и status ('
            #         + f'{homework_status}) в словаре не str.'
            #     )
            #     logger.error(message)
            #     raise TypeError(message)
            # else:
                # homework_name = homework['homework_name']
                # homework_status = homework['status']
            if homework_status not in HOMEWORK_VERDICTS:
                message = (
                    'В содержимом работы (homework) её статус '
                    + f'(homework_status) "{homework_status}" не '
                    + 'соответствует ожидаемым.'
                )
                logger.error(message)
                raise TypeError(message)
                # raise MyCustomError(message)
            else:
                verdict = HOMEWORK_VERDICTS[homework_status]
                # В случае успеха, функция возвращает подготовленную
                # для отправки в Telegram строку, содержащую один из
                # вердиктов словаря HOMEWORK_VERDICTS.
                return ('Изменился статус проверки работы '
                        + f'"{homework_name}". {verdict}')
    except TypeError as tperror:
        message = (
            f'Ошибка типа данных {tperror}. По ключам homework_name и status в словаре не str.'
        )
        logger.error(message)
        raise TypeError(message)


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
    # Токены проверяются в специальной функции - check_tokens() - к
    # моменту вызова send_message() она уже должна быть объявлена
    # (иначе мы просто завершаем программу). Даже если в ней ничего не
    # будет(None), то try-except это определить не поможет, такие
    # проверки обычно делаются через if-else.
    if not check_tokens():
        message = ('check_tokens() вернула не True, а вернула'
                   + f' {check_tokens()}.')
        logger.critical(message, exc_info=True)
        sys.exit(message)
    else:
        bot = Bot(token=TELEGRAM_TOKEN)
        # Переменная для хранения последней работы
        # Используется для проверки изменений
        current_homework = {}
        # current_homeworks = {}
        logger.info(
            f'current_homework из main - {current_homework}.'
        )
        # logger.info(f'current_homeworks из main - {current_homeworks}.')
        current_timestamp = 1646906700
        while True:
            try:
                # Сделать запрос к API.
                response = get_api_answer(current_timestamp)
                # Проверить ответ.
                homework = check_response(response)
                # homeworks = check_response(response)
                if homework != current_homework:
                # if homeworks != current_homeworks:
                    # Если есть обновления — получить статус работы из
                    # обновления и отправить сообщение в Telegram.
                    message = parse_status(homework)
                    # message = parse_status(homeworks)
                    send_message(bot, message)
                    current_homework = homework
                    logger.info(
                        f'current_homework из main - {current_homework}.'
                    )
                    # current_homework = homeworks
                    # current_homeworks = homeworks
                    time.sleep(RETRY_TIME)
                else:
                    message = 'Статус работы прежний.'
                    logger.debug(message)
                    send_message(bot, message)
                    # Подождать некоторое время и сделать новый запрос.
                    time.sleep(RETRY_TIME)
            except Exception as error:
                message = (
                    'Exception при запуске функции '
                    + f'main: {error}'
                )
                logger.error(message)
                send_message(bot, message)
                logger.exception(message, exc_info=True)
                raise MyCustomError(message)
            except ConnectionError as conerror:
                message = (
                    'ConnectionError при запуске функции main: '
                    + f'{conerror}'
                )
                logger.error(message)
                send_message(bot, message)
                logger.exception(message, exc_info=True)
                raise MyCustomError(message)
            except TypeError as typerror:
                message = (
                    'TypeError при запуске функции main: '
                    + f'{typerror}'
                )
                logger.error(message)
                send_message(bot, message)
                logger.exception(message, exc_info=True)
                raise MyCustomError(message)
            else:
                time.sleep(RETRY_TIME)
                message = 'Проверяем статус работы'
                send_message(bot, message)
            finally:
                message = 'Держись боец! Тяжёло в учении - легко в бою!'
                send_message(bot, message)


if __name__ == '__main__':
    # logger = logging.getLogger(__name__)  # Решил потренироваться в
    # создании отдельного логгера
    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s -'
        + ' %(funcName)s - %(lineno)d'
    )

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

    main()
