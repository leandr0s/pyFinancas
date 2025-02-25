import MetaTrader5 as mt5
import time
import pandas as pd

# Configurações do ativo e estratégia
SYMBOL = "GFSA3"  # Substitua pelo símbolo desejado
LOT = 100.0  # Tamanho do lote
TIMEFRAME = mt5.TIMEFRAME_M1  # Timeframe de 1 minuto
FAST_EMA = 5  # Período da EMA rápida
SLOW_EMA = 20  # Período da EMA lenta
PROFIT_MARGIN = 2.0  # Margem de lucro em reais
LOSS_THRESHOLD = -10.0  # Margem de prejuízo por operação
CONSECUTIVE_LOSS_THRESHOLD = 20  # Número de perdas consecutivas para venda
DELAY_LOSS = 500
DELAY = 10  # Intervalo entre execuções (em segundos)

# Inicializar MetaTrader 5
if not mt5.initialize():
    print("Erro ao inicializar MT5:", mt5.last_error())
    quit()

# Função para obter dados de mercado
def get_data(symbol, timeframe, n_bars):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_bars)
    if rates is None:
        print("Erro ao obter dados de mercado:", mt5.last_error())
        return None
    return pd.DataFrame(rates)

# Função para calcular EMA
def calculate_ema(data, period):
    return data['close'].ewm(span=period, adjust=False).mean()

# Função para abrir ordens
def open_order(symbol, lot, order_type):
    price = mt5.symbol_info_tick(symbol).ask if order_type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).bid
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
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

# Função para fechar posição
def close_position(position):
    order_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
    result = open_order(position.symbol, position.volume, order_type)
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"Posição fechada: {result}")
    else:
        print(f"Erro ao fechar posição: {result.retcode}")

# Loop principal
def main():
    loss_streak = 0

    while True:
        # Obter dados de mercado
        data = get_data(SYMBOL, TIMEFRAME, max(FAST_EMA, SLOW_EMA) + 1)
        if data is None or data.empty:
            time.sleep(DELAY)
            continue

        # Calcular EMA
        data['fast_ema'] = calculate_ema(data, FAST_EMA)
        data['slow_ema'] = calculate_ema(data, SLOW_EMA)

        # Últimos valores
        fast_ema = data['fast_ema'].iloc[-1]
        slow_ema = data['slow_ema'].iloc[-1]

        # Verificar posições abertas
        positions = mt5.positions_get(symbol=SYMBOL)
        if not positions:  # Não há posições abertas
            # Verificar gatilho de compra
            if fast_ema > slow_ema:  # EMA rápida cruzou acima da EMA lenta
                result = open_order(SYMBOL, LOT, mt5.ORDER_TYPE_BUY)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    print("Ordem de COMPRA enviada:", result)
            # Verificar gatilho de venda
            elif fast_ema < slow_ema:  # EMA rápida cruzou abaixo da EMA lenta
                result = open_order(SYMBOL, LOT, mt5.ORDER_TYPE_SELL)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    print("Ordem de VENDA enviada:", result)
        else:
            # Gerenciar posição aberta
            position = positions[0]
            profit = position.profit

            # Verificar condição de lucro
            if profit >= PROFIT_MARGIN:
                close_position(position)
                print(f"Lucro alcançado: {profit}. Posição fechada.")
                loss_streak = 0  # Resetar sequência de perdas

            # Verificar condição de prejuízo
            elif profit <= LOSS_THRESHOLD:
                loss_streak += 1
                print(f"Perda consecutiva {loss_streak}: {profit}")
                if loss_streak >= CONSECUTIVE_LOSS_THRESHOLD:
                    #close_position(position)
                    time.sleep(DELAY_LOSS)
                    print(f"Posição fechada após {loss_streak} perdas consecutivas.")
                    loss_streak = 0

        # Aguardar antes de repetir
        time.sleep(DELAY)

# Iniciar estratégia
try:
    main()
except KeyboardInterrupt:
    print("Estratégia finalizada pelo usuário.")
finally:
  mt5.shutdown()