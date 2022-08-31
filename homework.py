"""Главный файл приложения бота."""
import logging
import os
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

RETRY_TIME = 600
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
status_bank = get_api_answer_message_status_code_not_200


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат.

    Чат определяется переменной окружения TELEGRAM_CHAT_ID. Принимает
    на вход два параметра:
    - экземпляр класса Bot,
    - строку с текстом сообщения.
    """
    logger.info(f'Инициализируем объект bot - {bot}.')
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


def get_api_answer(current_timestamp):
    """Делает запрос к единственному эндпоинту API-сервиса.

    В качестве параметра функция получает временную метку.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    bot = Bot(token=TELEGRAM_TOKEN)
    global status_bank
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    status_code = response.status_code
    logger.info(f'status_code - {status_code}')
    if response.status_code != HTTPStatus.OK:
        message_status_code_not_200 = (
            f'Ошибка запроса к API. Код не равен 200. Код - {status_code}.'
        )
        if message_status_code_not_200 != status_bank:
            logger.error(message_status_code_not_200)
            send_message(bot, message_status_code_not_200)
            status_bank = message_status_code_not_200
        else:
            logger.error(message_status_code_not_200)
    else:
        # В случае успешного запроса должна вернуть ответ API,
        # преобразовав его из формата JSON к типам данных Python.
        response = response.json()
        return response


def check_response(response):
    """Проверяет ответ API на корректность.

    Если ответ API соответствует ожиданиям, то функция должна вернуть
    список домашних работ (он может быть и пустым), доступный в
    ответе API по ключу 'homeworks и приведенный к типам данных Python.
    """
    bot = Bot(token=TELEGRAM_TOKEN)
    if not isinstance(response, dict):
        message = 'Ответ АПИ (response) не словарь.'
        logger.error(message)
        raise TypeError(message)
    else:
        logger.info(f'response из check_response - {response}.')
        if 'homeworks' and 'current_date' not in response:
            message = ('В ответе АПИ отсутствует список работ и текущая дата'
                       + ' (ключи homeworks и current_date).')
            logger.error(message)
            send_message(bot, message)
            raise KeyError(message)
        else:
            homeworks = response['homeworks']
            if not isinstance(homeworks, list):
                message = 'Список работ (homeworkS) не list.'
                logger.error(message)
                send_message(bot, message)
                raise TypeError(message)
            else:
                if homeworks is None:
                    message = 'Список работ (homeworkS) пуст.'
                    logger.error(message)
                    send_message(bot, message)
                    raise ValueError(message)
                else:
                    homework = homeworks[0]
                    if not isinstance(homework, dict):
                        message = 'Содержимое работы (homeworK) не dict.'
                        logger.error(message)
                        raise TypeError(message)
                    else:
                        return homework


def parse_status(homework):
    """
    Парсит данные о домашних работах.

    Извлекает из информации о конкретной домашней работе статус этой
    работы. В качестве параметра функция получает только один элемент
    из списка домашних работ.
    """
    logger.info(f'homework из parse_status - {homework}.')
    logger.info(f'тип homework из parse_status - {type(homework)}.')
    if 'homework_name' not in homework:
        message = (
            'В содержимом работы (homework) нет имени и '
            + 'статуса работы (ключь homework_name).'
        )
        logger.error(message)
        raise KeyError(message)
    elif 'status' not in homework:
        message = (
            'В содержимом работы (homework) нет имени и '
            + 'статуса работы (ключь status).'
        )
        logger.error(message)
        raise KeyError(message)
    else:
        if not isinstance(
            ((homework['homework_name']) and (homework['status'])),
            str
        ):
            message = 'homework_name и status не str.'
            logger.error(message)
            raise TypeError(message)
        else:
            homework_name = homework['homework_name']
            homework_status = homework['status']
            if homework_status not in HOMEWORK_VERDICTS:
                message = (
                    'В содержимом работы (homework) её статус '
                    + f'(homework_status) "{homework_status}" не '
                    + 'соответствует ожидаемым.'
                )
                logger.error(message)
                raise KeyError(message)
            else:
                verdict = HOMEWORK_VERDICTS[homework_status]
                # В случае успеха, функция возвращает подготовленную
                # для отправки в Telegram строку, содержащую один из
                # вердиктов словаря HOMEWORK_VERDICTS.
                return ('Изменился статус проверки работы '
                        + f'"{homework_name}". {verdict}')


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
        current_homework = {}
        while True:
            try:
                bot = Bot(token=TELEGRAM_TOKEN)
                # Переменная для хранения последней работы
                # Используется для проверки изменений
                message = 'Проверяем статус работы'
                send_message(bot, message)
                logger.info(
                    f'current_homework из main - {current_homework}.'
                )
                current_timestamp = 1646906700
                # Сделать запрос к API.
                response = get_api_answer(current_timestamp)
                homework = check_response(response)
                if homework != current_homework:
                    # Если есть обновления — получить статус работы из
                    # обновления и отправить сообщение в Telegram.
                    message = parse_status(homework)
                    send_message(bot, message)
                    current_homework = homework
                    logger.info(
                        f'current_homework из main - {current_homework}.'
                    )
                    time.sleep(RETRY_TIME)
                else:
                    message = 'Статус работы прежний.'
                    logger.debug(message)
                    send_message(bot, message)
                    # Подождать некоторое время и сделать новый запрос.
                    time.sleep(RETRY_TIME)
            except ConnectionError as conerror:
                message = ('ConnectionError при запуске функции main: '
                           + f'{conerror}')
                logger.error(message)
                send_message(bot, message)
                logger.exception(message, exc_info=True)
                raise ConnectionError(message)
            except TypeError as typerror:
                message = (
                    'TypeError при запуске функции main: '
                    + f'{typerror}'
                )
                logger.error(message)
                send_message(bot, message)
                logger.exception(message, exc_info=True)
                raise TypeError(message)
            except Exception as error:
                message = (
                    'Exception при запуске функции '
                    + f'main: {error}.'
                )
                logger.error(message)
                send_message(bot, message)
                logger.exception(message, exc_info=True)
                raise MyCustomError(message)
            else:
                time.sleep(RETRY_TIME)
            finally:
                message = 'Держись боец! Тяжёло в учении - легко в бою!'
                send_message(bot, message)
                time.sleep(RETRY_TIME)


if __name__ == '__main__':
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
