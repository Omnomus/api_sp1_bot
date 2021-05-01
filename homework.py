import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.DEBUG,
                    filename='homework.log',
                    filemode='w',
                    format='%(asctime)s, %(levelname)s, %(lineno)d, %(name)s, %(message)s')
logger = logging.getLogger(__name__)

API_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
HW_STATUS = {'reviewing': 'Работа взята в ревью.',
             'approved': 'Ревьюеру всё понравилось, '
                         'можно приступать к следующему уроку.',
             'rejected': 'К сожалению в работе нашлись ошибки.',
             }

try:
    PRAKTIKUM_TOKEN = os.environ['PRAKTIKUM_TOKEN']
    TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
    CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
except KeyError as error:
    message = (f'Переменная {error} не найдена.'
               ' Программа не может быть запущена.')
    logging.error(message, exc_info=True)
    raise SystemExit


def get_homework_statuses(current_timestamp):
    """Make a request to API."""
    params = {'from_date': 0}
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    homework_statuses = requests.get(API_URL, params=params, headers=headers)
    try:
        homework_statuses.raise_for_status()
    except requests.exceptions.HTTPError as error:
        message = f'Проблема с запросом: {error}'
        logging.error(message, exc_info=True)
        return {}
    else:
        return homework_statuses.json()


def parse_homework_status(homework):
    """Get reviewer's verdict API answer."""
    try:
        homework_name = homework.get('homework_name')
        status = homework.get('status')
    except KeyError as error:
        message = f'В ответе API отсутствует поле {error}.'
        logging.error(message, exc_info=True)
        return {}
    except Exception as error:
        message = f' !!!!{error}.'
        logging.error(message, exc_info=True)
        return {}
    try:
        verdict = HW_STATUS[status]
    except KeyError as error:
        message = f'Статус домашней работы {error} не определен.'
        logging.error(message, exc_info=True)
        return {}
    else:
        return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def send_message(message, bot_client):
    """Send message with reviewer's verdict."""
    logging.info('Отправка сообщения')
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    """Start the bot."""
    logging.debug('Запуск бота')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(
                        new_homework.get('homeworks')[0]), bot)
            current_timestamp = new_homework.get(
                'current_date', current_timestamp)
            time.sleep(1200)
        except Exception as e:
            message = f'Бот столкнулся с ошибкой: {e}'
            logging.error(e, exc_info=True)
            send_message(message, bot)
            time.sleep(5)


if __name__ == '__main__':
    main()
