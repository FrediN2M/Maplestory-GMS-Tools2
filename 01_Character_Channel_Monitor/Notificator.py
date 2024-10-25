import requests
import time
from loguru import logger
import datetime


def telegram_message(telegram_api_url, bot_token, chat_id, timevar, seen_connections, ch_history):
    if seen_connections:
        msg = ch_history[-1]
        logger.info(msg)
        # Split the input string by dashes
        split_string = msg.split('-')
        # Extract the desired substring
        msg = split_string[-2].strip() + ' - ' + split_string[-1].strip()
    else:
        msg = 'Unknown'
    base_url = f'{telegram_api_url}{bot_token}/'
    if ch_history:
        # Send session information
        session_text = f'Session Started - {timevar}'
        send_telegram_message(base_url, chat_id, session_text)
        # Concatenate history items with [History] prefix and line breaks
        history_text = '\n'.join(f'[History] {item}' for item in ch_history[-20:])
        send_telegram_message(base_url, chat_id, history_text)
        # Send game closed message
        game_closed_text = 'Game Closed - ' + msg + ' - ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        send_telegram_message(base_url, chat_id, game_closed_text)
    else:
        logger.warning('Process is not running')


def send_telegram_message(base_url, chat_id, text):
    url = base_url + 'sendMessage'
    data = {
        'chat_id': chat_id,
        'text': text
    }

    while True:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            logger.info('Message sent successfully!')
            break
        else:
            logger.error(f'Failed to send message. Error code: {response.status_code}')
            # Wait for a few seconds before retrying
            time.sleep(2)


def webhook_message(mUrl, timevar, seen_connections, ch_history):
    if seen_connections:
        msg = ch_history[-1]
        logger.info(msg)
        # Split the input string by dashes
        split_string = msg.split('-')
        # Extract the desired substring
        msg = split_string[-2].strip() + ' - ' + split_string[-1].strip()
    else:
        msg = 'Unknown'
    if ch_history:
        # Send session information
        session_text = f'Session Started - {timevar}'
        send_webhook_message(mUrl, session_text)
        # Concatenate history items with [History] prefix and line breaks
        history_text = '\n'.join(f'[History] {item}' for item in ch_history[-20:])
        send_webhook_message(mUrl, history_text)
        # Send game closed message
        game_closed_text = 'Game Closed - ' + msg + ' - ' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        send_webhook_message(mUrl, game_closed_text)
    else:
        logger.warning('Process is not running')


def send_webhook_message(m_url, msg):
    # Ensure the message is formatted correctly
    data = {"content": msg}

    try:
        # Attempt to send the webhook request
        response = requests.post(m_url, json=data)

        # Check the response status code
        if response.status_code == 204:
            logger.info("info: Discord message sent successfully")
        else:
            logger.error(f"error: Failed to send Discord message. Status code: {response.status_code}, Response: {response.text}")

    except requests.exceptions.RequestException as e:
        logger.error(f"error: An exception occurred while sending the webhook: {e}")
