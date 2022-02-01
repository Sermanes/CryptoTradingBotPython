import telegram
from decouple import config

DATA_FILE = "data.csv"
EXCEPTION_FILE = "exception.txt"
EXCEPTION_DEFAULT_MESSAGE = "Una excepción ha ocurrido. Por favor revise el archivo de excepciones."

# write_file permite escribir en el archivo
def write_file(filename, data, n=True):
    f = open(filename, 'a')

    if n:
        f.write(data + '\n')
    else:
        f.write(data)


# send_telegram_message permite enviar el mensansaje a telegram directamente
def send_telegram_message(message):
    bot = telegram.Bot(token=config("API_TOKEN_TELEGRAM"))
    bot.send_message(chat_id=config("TELEGRAM_USER_ID"), text=message)


# register escribe sobre el archivo el resultado de la transacción
def add_order_to_history(new_order, price, quantity, pair):
    if new_order:
        text = 'Open {0}: {1}/{2} temporalidad: 1m'.format(
            pair, price, quantity)
        csv = '{0},{1},{2},'.format(pair, price, quantity)
        write_file(DATA_FILE, csv, False)
        send_telegram_message(text)
    else:
        text = 'Close {0}: {1}/{2}'.format(pair, price, quantity)
        csv = '{0},{1},{2}'.format(pair, price, quantity)
        write_file(DATA_FILE, csv)
        send_telegram_message(text)


# log_exception envia y registra los errores producidos en el programa
def log_exception(message):
    write_file(EXCEPTION_FILE, message)
    send_telegram_message(EXCEPTION_DEFAULT_MESSAGE)
