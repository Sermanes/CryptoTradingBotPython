import traceback
from binance import Client
from decouple import config
import telegram
import pandas as pd
import ta
import numpy as np
import time
import math


# Variables iniciales
symbols = ['BTC', 'ADA', 'BNB', 'ETH', 'XRP']
coin = 'BUSD'
pair = ''
leverage = 2
data_file = 'data.csv'
exception_file = 'exception.txt'
client = Client(config('API_KEY'), config('API_SECRET'), testnet=False)


# get_account_balance nos proporciona la informacion de nuestro usuario
def get_account_balance(i):
    balance = 0
    stats = client.futures_account_balance()

    for stat in stats:
        if stat['asset'] == coin:
            balance = float(stat['balance'])

    if balance <= 0 and i < 3:
        print('El balance no puede ser 0 o negativo, se volverá a comprobar. Balance obtenido: ', balance)
        time.sleep(1)
        get_account_balance(i + 1)
    if i > 3:
        print('Se ha superado el máximo número de intentos. El programa se cerrará.')
        exit()

    return balance


# get_minute_data nos ayuda a conseguir la informacion del par determinado anteriormente
def get_minute_data(pair, interval, lookback):
    frame = pd.DataFrame(client.futures_historical_klines(pair, interval, lookback + ' min ago UTC'))

    frame = frame.iloc[:, :6]
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)

    return frame


# Conseguir RSI, MACD y Estocastico del activo
def apply_technicals(df):
    df['%K'] = ta.momentum.stoch(df.High, df.Low, df.Close, window=14, smooth_window=3)
    df['%D'] = df['%K'].rolling(3).mean()
    df['rsi'] = ta.momentum.rsi(df.Close, window=14)
    df['macd'] = ta.trend.macd_diff(df.Close)
    df.dropna(inplace=True)


# open_order nos permite abrir una orden
def open_order(df):
    balance = get_account_balance(0)
    last_price = df.Close[-1]
    quantity = round(((balance / last_price) * leverage) * 0.75, 3)
    print('El bot comprara una cantidad de: ', quantity, ' ', pair)
    order = client.futures_create_order(symbol=pair, side='BUY', type="MARKET", quantity=quantity)
    register(True, last_price, quantity)

    return order['orderId'], quantity


# close_order nos permite cerrar nuestra orden
def close_order(quantity):
    client.futures_create_order(symbol=pair, side='SELL', type="MARKET", quantity=quantity)


# return_strategy_data nos devuelve los datos necesarios como rsi, macd...
def return_strategy_data(df):
    apply_technicals(df)
    last_position = df[-1:]
    rsi = float(last_position['rsi'])
    macd = float(last_position['macd'])
    stoch_k = float(last_position['%K'])
    stoch_d = float(last_position['%D'])
    price = float(last_position.Close)

    return rsi, macd, stoch_k, stoch_d, price


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
    bot.send_message(chat_id='600833782', text=message)


# register escribe sobre el archivo el resultado de la transacción
def register(new_order, price, quantity):
    if new_order:
        text = 'Open: ' + pair + ': ' + str(price) + '/' + str(quantity) + ' temp: 1m '
        write_file(data_file, text, False)
        send_telegram_message(text)
    else:
        text = 'Close: ' + pair + ': ' + str(price) + '/' + str(quantity)
        write_file(data_file, text, quantity)
        send_telegram_message(text)


# strategy es el core de la aplicación, contiene la logica de la estrategia
def strategy():
    data = get_minute_data(pair, '1m', '100')
    rsi, macd, stoch_k, stoch_d, price = return_strategy_data(data)
    print('El activo ', pair, ' se encuentra en los siguientes niveles: RSI:', rsi, ' MACD: ', macd,
            ' Estocastico: K/D ', stoch_k, '/', stoch_d)

    if (rsi <= 25.5) and (macd < 0) and (stoch_k <= 20) and (stoch_d <= 20):
        order_is_open = True
        order_id, quantity = open_order(data)
        order = client.futures_get_order(orderId=order_id, symbol=pair)
        open_price = float(order['avgPrice'])
        while order_is_open:
            minute_data = get_minute_data(pair, '1m', '100')
            rsi, macd, stoch_k, stoch_d, current_price = return_strategy_data(minute_data)
            print('El activo ', pair, ' en rango de 1m se encuentra en los siguientes niveles: RSI:', rsi,
                    ' MACD: ', macd, ' Estocastico: K/D ', stoch_k, '/', stoch_d)
            if stoch_k >= 80 or stoch_d >= 80:
                close_order(quantity)
                register(False, current_price, quantity)
                order_is_open = False
                continue
            if current_price <= (open_price * 0.995) or current_price >= (open_price * 1.005):
                close_order(quantity)
                register(False, current_price, quantity)
                order_is_open = False
                continue

            time.sleep(2)


while True:
    try:
        for symbol in symbols:
            pair = symbol + coin
            client.futures_change_leverage(leverage=leverage, symbol=pair)
            strategy()
    except:
        write_file(exception_file, traceback.format_exc())
        time.sleep(2)
        continue

    time.sleep(10)