import traceback
import time
import utils.registry as registry
import config.config as configuration
import utils.strategy as strategy
from binance import Client
from decouple import config


# Bucle encargado de realizar la estrategia
while True:
    try:
        client = Client(config('API_KEY'), config('API_SECRET'), testnet=False)
        decimals = configuration.get_decimals()
        for index, symbol in enumerate(configuration.get_symbols()):
            pair = symbol + configuration.get_coin()
            client.futures_change_leverage(leverage=configuration.get_leverage(), symbol=pair)
            strategy.run(client, pair, decimals[index])
    except:
        registry.log_exception(traceback.format_exc())
        time.sleep(2)
        continue

    time.sleep(5)