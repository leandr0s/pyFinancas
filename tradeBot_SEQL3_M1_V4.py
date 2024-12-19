import MetaTrader5 as mt5
import time
import pandas as pd

# Configurações ESTRATEIA DE MEDIAS MOVEIS EXPONECIAIS
SYMBOL = "SEQL3"  # Substitua pelo símbolo do ativo
LOT = 100.0  # Tamanho do lote
TIMEFRAME = mt5.TIMEFRAME_M1  # Timeframe de 1 minuto
FAST_EMA = 5  # Período da EMA rápida
SLOW_EMA = 20  # Período da EMA lenta
RSI_PERIOD = 14  # Período do RSI
TAKE_PROFIT = 100  # Take Profit em pontos
STOP_LOSS = 50  # Stop Loss em pontos
DELAY = 10  # Intervalo entre execuções (em segundos)

# Inicializar MT5
if not mt5.initialize():
    print("Erro ao inicializar MT5:", mt5.last_error())
    quit()

# Função para obter dados de mercado
def get_data(symbol, timeframe, n_bars):
    print("******************** RECUPERANDO DADOS")
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_bars)
    if rates is None:
        print("Erro ao obter dados de mercado:", mt5.last_error())
        return None
    return pd.DataFrame(rates)

# Função para calcular EMA
def calculate_ema(data, period):
    print("******************** CALCULO DO EMA")
    return data['close'].ewm(span=period, adjust=False).mean()

# Função para calcular RSI
def calculate_rsi(data, period):
    print("******************** CALCULO DO RSI")
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# Função para abrir ordens
def open_order(symbol, lot, order_type):
    print("******************** CRIANDO ORDEM")
    price = mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "sl": price - STOP_LOSS * mt5.symbol_info(symbol).point if order_type == mt5.ORDER_TYPE_BUY else price + STOP_LOSS * mt5.symbol_info(symbol).point,
        "tp": price + TAKE_PROFIT * mt5.symbol_info(symbol).point if order_type == mt5.ORDER_TYPE_BUY else price - TAKE_PROFIT * mt5.symbol_info(symbol).point,
        "deviation": 10,
        "magic": 123456,
        "comment": "Ordem automatizada",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Erro ao abrir ordem ({'COMPRA' if order_type == mt5.ORDER_TYPE_BUY else 'VENDA'}):", result.retcode)
    return result

# Função principal
def main():
    while True:
        # Obter dados de mercado
        data = get_data(SYMBOL, TIMEFRAME, max(FAST_EMA, SLOW_EMA, RSI_PERIOD) + 1)
        if data is None or data.empty:
            time.sleep(DELAY)
            continue

        # Calcular EMA e RSI
        data['fast_ema'] = calculate_ema(data, FAST_EMA)
        data['slow_ema'] = calculate_ema(data, SLOW_EMA)
        data['rsi'] = calculate_rsi(data, RSI_PERIOD)

        # Últimos valores
        fast_ema = data['fast_ema'].iloc[-1]
        slow_ema = data['slow_ema'].iloc[-1]
        rsi = data['rsi'].iloc[-1]

        # Verificar condições de compra/venda
        positions = mt5.positions_get(symbol=SYMBOL)
        if not positions:  # Se não houver posições abertas
            if fast_ema > slow_ema and rsi < 70:
                result = open_order(SYMBOL, LOT, mt5.ORDER_TYPE_BUY)
                print("#######################Ordem de COMPRA enviada:", result)
            elif fast_ema < slow_ema or rsi > 70:
                result = open_order(SYMBOL, LOT, mt5.ORDER_TYPE_SELL)
                print("########################Ordem de VENDA enviada:", result)
        else:
            print("Posição já aberta. Aguardando...")

        # Aguardar antes de repetir
        time.sleep(DELAY)

# Iniciar estratégia
try:
    main()
except KeyboardInterrupt:
    print("Estratégia finalizada pelo usuário.")
finally:
  mt5.shutdown()