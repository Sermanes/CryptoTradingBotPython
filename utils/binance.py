from time import time
import utils.registry as registry
import pandas as pd
import config.config as configuration

# get_account_balance nos proporciona la informacion de nuestro usuario
def get_account_balance(client, i):
    stats, balance = client.futures_account_balance(), 0

    for stat in stats:
        if stat['asset'] == configuration.get_coin():
            balance = float(stat['balance'])

    if balance <= 0 and i < 3:
        print('El balance no puede ser 0 o negativo, se volverá a comprobar. Balance obtenido: ', balance)
        time.sleep(1)
        get_account_balance(client, i+1)
    if i == 3:
        registry.send_telegram_message('Se ha superado el máximo número de intentos. El programa se cerrará.')
        exit()

    return balance


# get_minute_data nos ayuda a conseguir la informacion del par determinado anteriormente
def get_minute_data(client, pair, interval, lookback):
    frame = pd.DataFrame(client.futures_historical_klines(pair, interval, lookback + ' min ago UTC'))

    frame = frame.iloc[:, :6]
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame = frame.set_index('Time')
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)

    return frame


# open_order nos permite abrir una orden
def open_order(client, pair, decimals, df):
    balance = get_account_balance(client, 0)
    last_price = df.Close[-1]
    quantity = round(((balance / last_price) * configuration.get_leverage()) * 0.75, decimals)
    print('El bot comprara una cantidad de: ', quantity, ' ', pair)
    order = client.futures_create_order(symbol=pair, side='BUY', type="MARKET", quantity=quantity)
    registry.add_order_to_history(True, last_price, quantity, pair)

    return order['orderId'], quantity


# close_order nos permite cerrar nuestra orden
def close_order(client, pair, quantity):
    client.futures_create_order(symbol=pair, side='SELL', type="MARKET", quantity=quantity)