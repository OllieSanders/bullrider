from pandas import DataFrame
from technical.trendline import segtrends
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

from freqtrade.strategy.interface import IStrategy



class BullRider(IStrategy):
    minimal_roi = {
        "0": 0.30
    }

    stoploss = -0.05

    # Optimal ticker interval for the strategy
    ticker_interval = '15m'

    def populate_indicators(self, dataframe: DataFrame) -> DataFrame:
        #segs = segtrends(dataframe.tail(100), field='close', segments=5, charts=True)
        #dataframe['max_line'] = segs['Max Line']
        #dataframe['min_line'] = segs['Min Line']

        # RSI
        dataframe['rsi'] = ta.RSI(dataframe)

        # Bollinger bands
        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lowerband'] = bollinger['lower']
        dataframe['bb_middleband'] = bollinger['mid']
        dataframe['bb_upperband'] = bollinger['upper']

        charts = True
        field = 'close'
        no_nan = 100
        segments = 10
        x = dataframe[field]
        import numpy as np
        y = np.array(x)

        # Implement trendlines
        segments = int(segments)
        maxima = np.ones(segments)
        minima = np.ones(segments)
        segsize = int(len(y) / segments)
        for i in range(1, segments + 1):
            ind2 = i * segsize
            ind1 = ind2 - segsize
            maxima[i - 1] = max(y[ind1:ind2])
            minima[i - 1] = min(y[ind1:ind2])

        # Find the indexes of these maxima in the data
        x_maxima = np.ones(segments)
        x_minima = np.ones(segments)
        for i in range(0, segments):
            x_maxima[i] = np.where(y == maxima[i])[0][0]
            x_minima[i] = np.where(y == minima[i])[0][0]

        if charts:
            import matplotlib.pyplot as plt
            plt.plot(y)
            plt.grid(True)

        for i in range(0, segments - 1):
            maxslope = (maxima[i + 1] - maxima[i]) / (x_maxima[i + 1] - x_maxima[i])
            a_max = maxima[i] - (maxslope * x_maxima[i])
            b_max = maxima[i] + (maxslope * (len(y) - x_maxima[i]))
            maxline = np.linspace(a_max, b_max, len(y))

            minslope = (minima[i + 1] - minima[i]) / (x_minima[i + 1] - x_minima[i])
            a_min = minima[i] - (minslope * x_minima[i])
            b_min = minima[i] + (minslope * (len(y) - x_minima[i]))
            minline = np.linspace(a_min, b_min, len(y))

            if charts:
                plt.plot(maxline, 'g')
                plt.plot(minline, 'r')

        if charts:
            plt.show()

        dataframe['min_line'] = minline
        dataframe['max_line'] = maxline



        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['volume'] > 0) &
                (dataframe['bb_upperband'] < dataframe['bb_middleband'] * 1.01) & 
                (dataframe['rsi'] > dataframe['rsi'].shift(1)) &
                (dataframe['rsi'].shift(1) > dataframe['rsi'].shift(2)) &
                (dataframe['rsi'] > 30) &
                (dataframe['rsi'] < 50) &
                (dataframe['close'] < dataframe['min_line'] * 1.05)
            ),
            'buy'] = 1
        #dataframe.to_csv('user_data/trendline.csv')
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame) -> DataFrame:
        # different strategy used for sell points, due to be able to duplicate it to 100%
        dataframe.loc[
            (
                (dataframe['volume'] > 0) &
                (dataframe['close'] > dataframe['bb_upperband']) &
                (dataframe['rsi'].shift(1) > dataframe['rsi']) &
                (dataframe['rsi'] > 70) &
                (dataframe['close'] < dataframe['max_line'] * 0.90)
            ),
            'sell'] = 1
        return dataframe
