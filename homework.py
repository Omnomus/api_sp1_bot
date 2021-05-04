import json
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
                    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s')
logger = logging.getLogger(__name__)

API_URL = 'https://praktikum.yandex.ru/ap/user_api/homework_statuses/'
HW_STATUS = {'reviewing': 'Работа взята в ревью.',
             'approved': 'Ревьюеру всё понравилось, '
                         'можно приступать к следующему уроку.',
             'rejected': 'К сожалению в работе нашлись ошибки.',
             }
TIME_REQUEST = 1200
# TIME_ERROR = 60

try:
    PRAKTIKUM_TOKEN = os.environ['PRAKTIKUM_TOKEN']
    TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
    CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
except KeyError as error:
    message = (f'Переменная {error} не найдена.'
               ' Программа не может быть запущена.')
    logging.critical(message, exc_info=True)
    raise


def get_homework_statuses(current_timestamp):
    """Make a request to API."""
    params = {'from_date': current_timestamp}
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    homework_statuses = requests.get(API_URL, params=params, headers=headers)
    try:
        return homework_statuses.json()
    except json.decoder.JSONDecodeError:
        logging.error('error URL')
        return {}


def parse_homework_status(homework):
    """Get reviewer's verdict API answer."""
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    verdict = HW_STATUS.get(status)
    if (homework_name is None) or (status is None):
        logging.error('В ответе API нет нужных данных')
        return 'В ответе нет ничего про домашку :('
    elif verdict is None:
        logging.error('Неизвестный статус')
        return 'Статус домашки не знаком боту'
    else:
        return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def send_message(message, bot_client):
    """Send message with reviewer's verdict."""
    logging.info('Отправка сообщения')
    try:
        return bot_client.send_message(chat_id=CHAT_ID, text=message)
    except Exception as error:
        logging.error(f'Бот не смог отправить сообщение - {error}')


def main():
    """Start the bot."""
    logging.debug('Запуск бота')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    if bot:
        logging.info('Бот создан')
        message = 'Привет! Начинаю отслеживать твою домашку!'
        send_message(message, bot)
    else:
        logging.error('Ошибка с созданием бота')
    current_timestamp = int(time.time())

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                message = parse_homework_status(
                    new_homework.get('homeworks')[0])
                send_message(message, bot)
            current_timestamp = new_homework.get(
                'current_date', current_timestamp)
        except Exception as e:
            message = f'Бот столкнулся с ошибкой: {e}'
            logging.error(message, exc_info=True)
            send_message(message, bot)
        finally:
            time.sleep(TIME_REQUEST)


if __name__ == '__main__':
    main()
