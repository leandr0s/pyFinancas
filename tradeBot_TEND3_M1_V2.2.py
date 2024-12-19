import MetaTrader5 as mt5
import pandas as pd
import time
from datetime import datetime, timedelta



mt5.initialize()
cont_venda = 0
idx_venda = 10
sleep = 10
ticker = "TEND3"
volume = 100.0
margem = 3
prejuizo = -10

while True:

    #garante q cont_vendas vai ser reinicializado
    if cont_venda >= idx_venda: cont_venda = 0
    
    intervalo = mt5.TIMEFRAME_M1
    data_final = datetime.today()
    data_inicial = datetime.today() - timedelta(days = 10)
    mt5.symbol_select(ticker)

    def realizaLucro(ticker):
        order =None
        if (float(get_preco_corrente(ticker))-float(get_preco_compra(ticker)))*volume >= margem:
            order = realizaVenda(ticker)
            print("******************** LUCRO REALIZADO")
        else: print("******************** FORA DA MARGEM LUCRO")
        return order
    
    def gravaUltimaCompra(ticker,order):
        #print(order[-1][5])
        df_cotacao = pd.DataFrame(order[-1])
        #print(df_cotacao)
        df_cotacao.to_csv('dados/cotacoes_'+ticker+'.csv', sep=';', index=None)

    def get_preco_compra(ticker):
        df = pd.read_csv('dados/cotacoes_'+ticker+'.csv' , sep=';')
        #print(df)
        return df.iloc[5].iloc[0]

    def get_preco_corrente(ticker):
        #Obtém o preço atual do ativo.
        t = mt5.symbol_info_tick(ticker)
        if t is None:
            print(f"Erro ao obter o preço atual: {mt5.last_error()}")
            return None
        return t.bid  # Preço de compra atual


    def verificaVenda(ticker,cont_venda):
        if (float(get_preco_corrente(ticker))-float(get_preco_compra(ticker)))*volume <= prejuizo:
            if cont_venda >= idx_venda :
                realizaVenda(ticker)
            else: 
                print("CONTANDO "+str(cont_venda)+" PRA VENCER O ATIVO -> "+ticker)
                cont_venda = cont_venda + 1
        return cont_venda 
    
    def realizaVenda(ticker):
        preco_de_tela = mt5.symbol_info(ticker).bid
        ordem_venda = {
            "action": mt5.TRADE_ACTION_PENDING, #trade a mercado
            "symbol": ticker,
            "volume": volume,
            "type": mt5.ORDER_TYPE_SELL,
            "price": get_preco_corrente(ticker),
            "type_time": mt5.ORDER_TIME_DAY, #so manda a ordem se o mercado tiver aberto
            "type_filling": mt5.ORDER_FILLING_RETURN,                                                             }
        orderm_send = mt5.order_send(ordem_venda)

        print("VENDEU O ATIVO -> "+ticker)
        return orderm_send

    def pegando_dados(ativo_negociado, intervalo, data_de_inicio, data_fim):

        dados = mt5.copy_rates_range(ativo_negociado, intervalo, data_de_inicio, data_fim)
        dados = pd.DataFrame(dados)
        #print(dados)
        dados["time"] = pd.to_datetime(dados["time"], unit = "s")
        return dados


    dados_atualizados = pegando_dados(ticker, intervalo, data_inicial, data_final)

    def estrategia_trade(dados, ativo, cont_venda, idx_venda):

        #se a média rápida for maior do que média lenta, eu vou comprar.

        dados["media_rapida"] = dados["close"].rolling(7).mean()
        dados["media_devagar"] = dados["close"].rolling(40).mean()

        ultima_media_rapida = dados["media_rapida"].iloc[-1]
        ultima_media_devagar = dados["media_devagar"].iloc[-1]

        print(f"Última Média Rápida: {ultima_media_rapida} | Última Média Devagar: {ultima_media_devagar}")

        #ultima_media_rapida = 4

        posicao = mt5.positions_get(symbol = ativo)

        #print('posição-> '+str(posicao))

        if ultima_media_rapida > ultima_media_devagar:

            if len(posicao) == 0:

                preco_de_tela = mt5.symbol_info(ativo).ask

                ordem_compra = {
                    "action": mt5.TRADE_ACTION_DEAL, #trade a mercado
                    "symbol": ativo,
                    "volume": volume,
                    "type": mt5.ORDER_TYPE_BUY,
                    "price": preco_de_tela,
                    "type_time": mt5.ORDER_TIME_DAY, #so manda a ordem se o mercado tiver aberto
                    "type_filling": mt5.ORDER_FILLING_RETURN,
                                                                    }
                
                order_send = mt5.order_send(ordem_compra)
                gravaUltimaCompra(ticker,order_send)
                print("COMPROU O ATIVO -> "+ticker)

        elif ultima_media_rapida <= ultima_media_devagar:
                if len(posicao) != 0:
                    cont_venda = verificaVenda(ticker,cont_venda)                    
        return cont_venda


    cont_venda = estrategia_trade(dados_atualizados, ticker, cont_venda, idx_venda)
    realizaLucro(ticker)
    print("######################## preco atual "+str(get_preco_corrente(ticker)))
    print("######################## preco compra "+str(get_preco_compra(ticker)))
    print("######################## diferenca "+str((float(get_preco_corrente(ticker))-float(get_preco_compra(ticker)))*volume))

    time.sleep(sleep)






















