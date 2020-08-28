import threading
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime
from blqt.backtest.utils import *
import warnings

warnings.filterwarnings(action="ignore")


class Logger(object):
    def __init__(self):
        self.sys = None

    def log(self, *args, **kwargs):
        pass

    def set_system(self, sys):
        self.sys = sys


class CLIAsyncLogger(Logger):
    def __init__(self):
        super(CLIAsyncLogger, self).__init__()
        self.log_queue = []
        self.log_thread = threading.Thread(target=self.log)

    def log(self):
        while self.switch:
            for log in self.log_queue:
                print("[LOG] ", log)
                self.log_queue.remove(log)

    def toggle(self, switch=True):
        self.switch = switch
        if switch is True:
            self.log_thread.start()


class BasicLogger(Logger):
    def __init__(self, benchmark_ticker):
        super(BasicLogger, self).__init__()
        self.benchmark_lst = []
        self.pv_lst = []
        self.timestamp_lst = []
        self.benchmark_ticker = benchmark_ticker

    def set_system(self, sys):
        super(BasicLogger, self).set_system(sys)
        self.timeframe = min(self.sys.data_provider.ohlcv_data[self.benchmark_ticker].keys())

    def log(self):
        self.pv_lst.append(self.sys.broker.pv)
        self.benchmark_lst.append(self.sys.data_provider.current(self.benchmark_ticker, "close", self.timeframe))
        self.timestamp_lst.append(self.sys.broker.indexer.timestamp)

    def _result(self, pnl_freq="1M"):
        if self.sys is not None:
            self.trade_hist_rate = self.sys.broker.trade_hist_rate
            self.trade_hist = self.sys.broker.trade_hist

        self.pv_lst = np.array(self.pv_lst)

        self.win_lst = list(filter(lambda x: x > 0, self.trade_hist))
        self.lose_lst = list(filter(lambda x: x < 0, self.trade_hist))

        _, self.best_month, self.worse_month, self.mean_monthly_pnl_perc = \
            calc_freq_pnl(pv_lst=self.pv_lst, timestamp_lst=self.timestamp_lst, freq=pnl_freq)

        self.cagr = calc_cagr(self.pv_lst, self.timestamp_lst)

        self.sharpe_ratio, self.sortino_ratio = calc_sharpe_sortino_ratio(self.pv_lst, self.benchmark_lst,
                                                                          self.timestamp_lst)

    def result(self, pnl_freq="1M"):
        self._result(pnl_freq)

        self.trade_hist_rate = np.array(self.trade_hist_rate)
        return (
            f"""
            overall p&L(%): {np.round(self.pv_lst[-1] / self.pv_lst[0] * 100 - 100, 2)}%
            MDD(%): {np.round(get_mdd(self.pv_lst)[-1] * 100, 2)}%
            CAGR(%): {np.round(self.cagr, 2)}%\n

            sharpe ratio: {np.round(self.sharpe_ratio, 2)}
            sortino ratio: {np.round(self.sortino_ratio, 2)}\n

            p&l rate: {np.round(-np.mean(self.win_lst) / np.mean(self.lose_lst), 2)}
            win rate: {np.round(len(self.win_lst) / len(self.trade_hist) * 100, 2)}%
            lose rate: {np.round(len(self.lose_lst) / len(self.trade_hist) * 100, 2)}%\n

            best {pnl_freq} p&L(%): {np.round(self.best_month, 2)}%
            worst {pnl_freq} p&L(%): {np.round(self.worse_month, 2)}%
            average {pnl_freq} p&L(%): {np.round(self.mean_monthly_pnl_perc, 2)}%\n

            average p&L(%) per trade: {np.round(np.mean(self.trade_hist_rate) * 100, 2)} %
            max p&L(%) per trade: {np.round(np.max(self.trade_hist_rate) * 100, 2)} %
            min p&L(%) per trade: {np.round(np.min(self.trade_hist_rate) * 100, 2)} %
            average profit per trade: {np.round(np.mean(self.trade_hist_rate[np.where(self.trade_hist_rate > 0)])*100, 2)}%
            average loss per trade: {np.round(np.mean(self.trade_hist_rate[np.where(self.trade_hist_rate < 0)])*100, 2)}%\n

            number of trades:{len(self.trade_hist)}"""
        )

    def plot_relative(self):
        x = [datetime.datetime.fromtimestamp(d) for d in self.timestamp_lst]
        plt.plot(x, np.array(self.pv_lst) / self.pv_lst[0], label="portfolio")
        plt.plot(x, np.array(self.benchmark_lst) / self.benchmark_lst[0], label="benchmark")
        plt.legend()
        plt.show()


class LiveLogger(BasicLogger):
    def __init__(self, *args, **kwargs):
        super(LiveLogger, self).__init__(*args, **kwargs)
        plt.ion()

    def plot_relative(self):
        plt.clf()
        plt.plot(self.timestamp_lst, np.array(self.pv_lst) / self.pv_lst[0], label="portfolio")
        plt.plot(self.timestamp_lst, np.array(self.benchmark_lst) / self.benchmark_lst[0], label="benchmark")
        plt.legend()
        plt.pause(1e-20)

    def log(self):
        super(LiveLogger, self).log()
        self.plot_relative()
