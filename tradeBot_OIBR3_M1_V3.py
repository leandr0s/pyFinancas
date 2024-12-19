import MetaTrader5 as mt5
import time
import pandas as pd

# Configurações do ativo e estratégia MEDIA MOVEL COM GRANTIA DE GANHOS E CONTROLE DE PERDAS
SYMBOL = "OIBR3"  # Substitua pelo símbolo desejado
LOT = 100.0  # Tamanho do lote
TIMEFRAME = mt5.TIMEFRAME_M1  # Timeframe de 1 minuto
MA_PERIOD = 14  # Período da média móvel
PROFIT_TARGET = 3.0  # Lucro-alvo em reais
LOSS_THRESHOLD = -10.0  # Limite de prejuízo por operação
CONSECUTIVE_LOSS_THRESHOLD = 10  # Número de perdas consecutivas para vender

# Inicializar MT5
if not mt5.initialize():
    print("Erro ao inicializar MT5:", mt5.last_error())
    quit()

# Função para obter dados de mercado
def get_data(symbol, timeframe, n_bars):
    print("******************** OBTENDO DADOS")
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_bars)
    if rates is None:
        print("Erro ao obter dados de mercado:", mt5.last_error())
        return None
    return pd.DataFrame(rates)

# Função para calcular média móvel
def calculate_ma(data, period):
    print("******************** CALCULA MEDIA MOVEL")
    return data['close'].rolling(window=period).mean()

# Função para executar compra
def buy(symbol, lot):
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY,
        "price": mt5.symbol_info_tick(symbol).ask,
        "deviation": 10,
        "magic": 123456,
        "comment": "Compra automatizada",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("Erro ao executar compra:", result.retcode)
    else: print("################# LUCRO REALIZADO")
    return result

# Função para executar venda
def sell(symbol, lot):
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_SELL,
        "price": mt5.symbol_info_tick(symbol).bid,
        "deviation": 10,
        "magic": 123456,
        "comment": "Venda automatizada",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print("Erro ao executar venda:", result.retcode)
    else: print("#################### REALIZA VENDA")
    return result

# Loop principal
loss_streak = 0

while True:
    # Obter dados recentes
    data = get_data(SYMBOL, TIMEFRAME, MA_PERIOD + 1)
    if data is None or data.empty:
        time.sleep(10)
        continue

    # Calcular média móvel
    data['ma'] = calculate_ma(data, MA_PERIOD)
    last_close = data['close'].iloc[-1]
    last_ma = data['ma'].iloc[-1]

    # Verificar gatilho de compra
    if last_close > last_ma:  # Preço cruzou para cima da média móvel
        buy_result = buy(SYMBOL, LOT)
        if buy_result and buy_result.retcode == mt5.TRADE_RETCODE_DONE:
            print("Compra realizada:", buy_result)

    # Obter posição aberta
    positions = mt5.positions_get(symbol=SYMBOL)
    if positions:
        position = positions[0]
        profit = position.profit

        # Verificar condição de lucro
        if profit >= PROFIT_TARGET:
            sell_result = sell(SYMBOL, LOT)
            if sell_result and sell_result.retcode == mt5.TRADE_RETCODE_DONE:
                print("******************** Venda realizada com lucro:", sell_result)
                loss_streak = 0  # Resetar a sequência de perdas

        # Verificar condição de prejuízo
        elif profit <= LOSS_THRESHOLD:
            loss_streak += 1
            if loss_streak >= CONSECUTIVE_LOSS_THRESHOLD:
                sell_result = sell(SYMBOL, LOT)
                if sell_result and sell_result.retcode == mt5.TRADE_RETCODE_DONE:
                    print("******************* Venda realizada após sequência de perdas:", sell_result)
                    loss_streak = 0

    # Esperar 10 segundos antes do próximo loop
    time.sleep(10)
