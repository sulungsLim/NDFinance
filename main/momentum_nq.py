from blqt.backtest.data_providers import BacktestDataProvider
from blqt.backtest.historical_data import TimeIndexedData
from blqt.backtest.stratagies import *
from blqt.backtest.brokers import BackTestBroker
from blqt.backtest.loggers import BasicLogger
from blqt.backtest.base import *
from talib import abstract as ta


def first_test(data_path):
    df = pd.read_csv(data_path).iloc[:]
    df.columns = [c.lower() for c in df.columns]
    df["timestamp"] = [time.mktime(datetime.datetime.strptime(t, "%Y-%m-%d %H:%M:%S").timetuple()) for t in
                       df["timestamp"].tolist()]

    data = TimeIndexedData()
    data.from_pandas(df)

    data.add_array("MA200", ta.SMA(df["close"], timeperiod=200 * 60))
    data.add_array("MA50", ta.SMA(df["close"], timeperiod=50 * 60))
    data.add_array("ADX", ta.ADX(df["high"], df["low"], df["close"], timeperiod=14 * 5))
    data.add_array("momentum", ta.MOM(df["close"], timeperiod=60))

    indexer = TimeIndexer(df["timestamp"].values)

    data_provider = BacktestDataProvider()
    data_provider.register_time_indexer(indexer)
    data_provider.register_ohlcv_data("NQ", data)

    broker = BackTestBroker(data_provider, indexer)
    broker.initialize(margin=10000000)

    NQ = FinancialProduct("NQ", 0.25, 4, 0.0001, 0.1, 0.9, 1)

    broker.add_ticker(NQ)

    system = BacktestSystem()

    stratagy = ActualMomentumStratagy(leverage=1, rebalance_period=60*60*24*14)

    logger = BasicLogger("NQ")

    system.set_broker(broker)
    system.set_data_provider(data_provider)
    system.set_logger(logger)
    system.set_stratagy(stratagy)
    system.run()

    system.result()
    system.plot()


if __name__ == '__main__':
    first_test("../data/NQ_2017_2020.csv")