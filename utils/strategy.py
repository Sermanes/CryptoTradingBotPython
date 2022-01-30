from time import time
import utils.analysis as analysis
import utils.binance as binance
import utils.registry as registry

# stop_loss_take_profit normas para ejecutar la opcion de venta
def stop_loss_take_profit(client, pair, quantity, open_price):
    order_is_open = True
    while order_is_open:
        minute_data = binance.get_minute_data(client, pair, '1m', '100')
        rsi, macd, stoch_k, stoch_d, current_price = analysis.return_strategy_data(minute_data)
        print('El activo ', pair, ' en rango de 1m se encuentra en los siguientes niveles: RSI:', rsi,
                ' MACD: ', macd, ' Estocastico: K/D ', stoch_k, '/', stoch_d)
        if stoch_k >= 80 or stoch_d >= 80:
            binance.close_order(client, quantity)
            registry.add_order_to_history(False, current_price, quantity)
            order_is_open = False
            continue
        if current_price <= (open_price * 0.995) or current_price >= (open_price * 1.005):
            binance.close_order(client, quantity)
            registry.add_order_to_history(False, current_price, quantity)
            order_is_open = False
            continue

        time.sleep(1)


# strategy es el core de la aplicación, contiene la logica de la estrategia
def run(client, pair, decimals):
    data = binance.get_minute_data(client, pair, '1m', '100')
    rsi, macd, stoch_k, stoch_d, price = analysis.return_strategy_data(data)
    print('El activo ', pair, ' se encuentra en los siguientes niveles: RSI:', rsi, ' MACD: ', macd,
            ' Estocastico: K/D ', stoch_k, '/', stoch_d)

    if (rsi <= 25.5) and (macd < 0) and (stoch_k <= 20) and (stoch_d <= 20):
        order_id, quantity = binance.open_order(client, pair, decimals, data)
        order = client.futures_get_order(orderId=order_id, symbol=pair)
        open_price = float(order['avgPrice'])
        stop_loss_take_profit(client, pair, quantity, open_price)