import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def get_homework_statuses(current_timestamp):
    """Make a request to API."""
    params = {'from_date': 0}
    headers = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
    homework_statuses = requests.get(
        'https://praktikum.yandex.ru/api/user_api/homework_statuses/',
        params=params,
        headers=headers)
    return homework_statuses.json()


def parse_homework_status(homework):
    """Get reviewer's verdict API answer."""
    homework_name = homework.get('homework_name')
    if homework.get('status') != 'approved':
        verdict = 'К сожалению в работе нашлись ошибки.'
    else:
        verdict = ('Ревьюеру всё понравилось, '
                   'можно приступать к следующему уроку.')
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
            time.sleep(120)

        except Exception as e:
            print(f'Бот столкнулся с ошибкой: {e}')
            logging.error(e, exc_info=True)
            send_message(e, bot)
            time.sleep(5)


if __name__ == '__main__':
    main()
