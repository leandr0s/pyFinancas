import MetaTrader5 as mt5
import pandas as pd
import time
from datetime import datetime, timedelta



mt5.initialize() 
cont_venda = 0
idx_venda = 10


while True:


    ticker = "AZUL4"
    intervalo = mt5.TIMEFRAME_M5
    data_final = datetime.today()
    data_inicial = datetime.today() - timedelta(days = 10)
    mt5.symbol_select(ticker)
    

    def verificaVenda(total_vendas):
        cont_venda = total_vendas + 1
        return cont_venda
    
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


        print('posição-> '+str(posicao))

        if ultima_media_rapida > ultima_media_devagar:

            if len(posicao) == 0:

                preco_de_tela = mt5.symbol_info(ativo).ask

                ordem_compra = {
                    "action": mt5.TRADE_ACTION_DEAL, #trade a mercado
                    "symbol": ativo,
                    "volume": 100.0,
                    "type": mt5.ORDER_TYPE_BUY,
                    "price": preco_de_tela,
                    "type_time": mt5.ORDER_TIME_DAY, #so manda a ordem se o mercado tiver aberto
                    "type_filling": mt5.ORDER_FILLING_RETURN,
                                                                    }
                
                mt5.order_send(ordem_compra)

                print("COMPROU O ATIVO -> "+ticker)

        elif ultima_media_rapida <= ultima_media_devagar:

                if len(posicao) != 0:
                    cont_venda = verificaVenda(cont_venda)
                    if cont_venda >= idx_venda :
                        preco_de_tela = mt5.symbol_info(ativo).bid

                        ordem_venda = {
                            "action": mt5.TRADE_ACTION_DEAL, #trade a mercado
                            "symbol": ativo,
                            "volume": 100.0,
                            "type": mt5.ORDER_TYPE_SELL,
                            "price": preco_de_tela,
                            "type_time": mt5.ORDER_TIME_DAY, #so manda a ordem se o mercado tiver aberto
                            "type_filling": mt5.ORDER_FILLING_RETURN,
                                                                            }
                        
                        mt5.order_send(ordem_venda)

                        print("VENDEU O ATIVO -> "+ticker)
                    else: print("CONTANDO "+str(cont_venda)+" PRA VENCER O ATIVO -> "+ticker)
        return cont_venda


    cont_venda = estrategia_trade(dados_atualizados, ticker, cont_venda, idx_venda)

    time.sleep(70)






















