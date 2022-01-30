import ta

# Conseguir RSI, MACD y Estocastico del activo
def apply_technicals(df):
    df['%K'] = ta.momentum.stoch(df.High, df.Low, df.Close, window=14, smooth_window=3)
    df['%D'] = df['%K'].rolling(3).mean()
    df['rsi'] = ta.momentum.rsi(df.Close, window=14)
    df['macd'] = ta.trend.macd_diff(df.Close)
    df.dropna(inplace=True)


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