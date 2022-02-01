import time
import math
import utils.analysis as analysis
import utils.binance as binance
import utils.registry as registry
import config.config as configuration



def stocastic_movement_sell(data, stoch_k, stoch_d, open_price, current_price):
    k = data['%K'].iloc[-2]
    d = data['%D'].iloc[-2]
    kk = data['%K'].iloc[-3]
    dd = data['%D'].iloc[-3]
    k_mean = (k + kk)/2
    d_mean = (d + dd)/2

    if (stoch_k - k_mean >= 50) or (stoch_d - d_mean >= 50):
        # No siempre que hay un movimiento alcista brusco otorga ganancias, en ese caso
        # dejamos que actue mejor el SL que vender en perdidas
        if open_price < current_price:
            registry.send_telegram_message('Se vende por movimiento brusco')
            return True
        
    if stoch_k >= 75 or stoch_d >= 75:
        if open_price < current_price:
            registry.send_telegram_message('El estocástico alcanzo 75 puntos')
            return True
    
    return False


# stop_loss_take_profit normas para ejecutar la opcion de venta
def stop_loss_take_profit(client, pair, quantity, open_price):
    order_is_open = True
    while order_is_open:
        minute_data = binance.get_minute_data(client, pair, '1m', '100')
        rsi, macd, stoch_k, stoch_d, current_price = analysis.return_strategy_data(
            minute_data)
        print('El activo comprado {0} se encuentra en los siguientes niveles: RSI: {1}, MACD: {2}, Estocástico: {3}/{4}'.format(
            pair, rsi, macd, stoch_k, stoch_d))
        if stocastic_movement_sell(minute_data, stoch_k, stoch_d, open_price, current_price):
            binance.close_order(client, pair, quantity)
            registry.add_order_to_history(False, current_price, quantity, pair)
            order_is_open = False
            continue
        # Take profit en 1,005 y Stoploss en 0.995
        if current_price <= (open_price * 0.995) or current_price >= (open_price * 1.005):
            binance.close_order(client, pair, quantity)
            registry.add_order_to_history(False, current_price, quantity, pair)
            order_is_open = False
            continue

        time.sleep(1)

# exponencial probability 1-e^(-x/B)
# @see https://en.wikipedia.org/wiki/Exponential_distribution
def density_function(x, b):
    return (1-math.e**(-x/b))


# rsi_probability devuelve la probabilidad de que rebote el valor, cuanto más cercano a 0
# mas probabilidad de que rebote.
def rsi_probability(rsi):
    return  (100 - (density_function(rsi, 100)*100))*0.55


# stoch_probability devuelve la probabilidad de que rebote el valor, cuanto más cercano a 0
# mas probabilidad de que rebote.
def stoch_probability(stoch_k, stoch_d):
    m = (stoch_k+stoch_d)/2
    return  (100 - (density_function(m, 100)*100))*0.35


# macd_probability devuelve la probabilidad de que rebote el valor, cuanto más cercano al menor macd registrado
# en los últimos movimientos aumentando la probabilidad de que rebote.
def macd_probability(df, macd):
    if macd < 0:
        minimum = df['macd'].min()
        return ((macd/minimum)*100)*0.1

    return 0


# calculate_probability suma las probabilidades de los indicadores y devuelve la probabilidad de que el moviemiento
# sea correcto
def calculate_probability(client, pair):
    data = binance.get_minute_data(client, pair, '1m', '100')
    rsi, macd, stoch_k, stoch_d, price = analysis.return_strategy_data(data)
    probability = rsi_probability(rsi) + stoch_probability(stoch_k, stoch_d) + macd_probability(data, macd)
    print('El activo {0} se encuentra en los siguientes niveles: RSI: {1}, MACD: {2}, Estocástico: {3}/{4}, probabilidad: {5}%'.format(
        pair, round(rsi, 4), round(macd, 4), round(stoch_k, 4), round(stoch_d, 4), round(probability, 2)))
    
    return probability, data



# strategy es el core de la aplicación, contiene la logica de la estrategia
def run(client, pair, decimals):
    probability, data = calculate_probability(client, pair)
    if  probability >= configuration.get_probability():
        order_id, quantity = binance.open_order(client, pair, decimals, data)
        order = client.futures_get_order(orderId=order_id, symbol=pair)
        open_price = float(order['avgPrice'])
        stop_loss_take_profit(client, pair, quantity, open_price)
