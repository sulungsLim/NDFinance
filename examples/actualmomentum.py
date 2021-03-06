from ndfinance.brokers.backtest import *
from ndfinance.core import BacktestEngine
from ndfinance.analysis.backtest.analyzer import BacktestAnalyzer
from ndfinance.analysis.technical import RateOfChange
from ndfinance.visualizers.backtest_visualizer import BasicVisualizer
from ndfinance.strategies.trend import ActualMomentumStratagy
from ndfinance.callbacks import PositionWeightPrinterCallback
import matplotlib.pyplot as plt


def main(tickers, paths=None, n=2000, **kwargs):
    path="./bt_results/actualmomentum/"
    dp = BacktestDataProvider()
    if path is None:
        dp.add_yf_tickers(*tickers)
    else:
        dp.add_ohlc_dataframes(paths, tickers)
    dp.add_technical_indicators(tickers, [TimeFrames.day], [RateOfChange(n)])

    indexer = TimeIndexer(dp.get_shortest_timestamp_seq())
    dp.set_indexer(indexer)
    dp.cut_data()

    brk = BacktestBroker(dp, initial_margin=10000)
    [brk.add_asset(Asset(ticker=ticker)) for ticker in tickers]

    strategy = ActualMomentumStratagy(
        momentum_threshold=1, 
        rebalance_period=TimeFrames.hour,
        momentum_label=f"ROCR{n}",
    )

    engine = BacktestEngine()
    engine.register_broker(brk)
    engine.register_strategy(strategy)
    #engine.register_callback(PositionWeightPrinterCallback())

    log = engine.run()
    
    analyzer = BacktestAnalyzer(log)
    analyzer.print()
    analyzer.export(path=path)

    visualizer = BasicVisualizer()
    visualizer.plot_log(log)

    visualizer.export(path=path)

if __name__ == '__main__':
    main(
        [
            "XBTUSD",
            "ETHUSD"
        ],
        [
            "/home/bellmanlabs/Data/bitmex/trade/ohlc/10T/XBTUSD.csv",
            "/home/bellmanlabs/Data/bitmex/trade/ohlc/10T/ETHUSD.csv"
        ]
    )