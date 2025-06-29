import pandas as pd

from candlestickpattern.one_two_three_pattern import OneTwoThreePattern
from strategy_profile_enum import StrategyProfileEnum


class InvestmentStrategy:
    def __init__(self, profile:StrategyProfileEnum, dataframe:pd.DataFrame, trades:list):
        if profile == StrategyProfileEnum.POSITION:
            self.pattern_detector = OneTwoThreePattern(dataframe, trades)

    def apply(self):

        self.pattern_detector.validate()


def detect_bollinger_cci_strategy(df, trades):
    active_setup = None

    for i in range(2, len(df) - 1): # monitors candles day by day
        today = df.iloc[i]
        yesterday = df.iloc[i-1]
        two_days_ago = df.iloc[i-2]

        # 1️⃣ Check for trigger setup
        if active_setup is None:
            if today["close"] <= today["Lower Band"]:
                active_setup = {"type": "BUY", "trigger_index": i}
            elif today["close"] >= today["Upper Band"]:
                active_setup = {"type": "SELL", "trigger_index": i}

        # 2️⃣ After trigger: Check CCI cross within 2 candles
        if active_setup:
            days_since_trigger = i - active_setup["trigger_index"]

            if 1 <= days_since_trigger <= 2:
                # Calculate CCI and its SMA(5)
                cci_now = today["cci_fast"]
                cci_yesterday = yesterday["cci_fast"]
                cci_sma_now = df["cci_fast"].rolling(5).mean().iloc[i]
                cci_sma_yesterday = df["cci_fast"].rolling(5).mean().iloc[i-1]

                if active_setup["type"] == "BUY":
                    if cci_yesterday < cci_sma_yesterday and cci_now > cci_sma_now:
                        active_setup["entry_signal_index"] = i
                elif active_setup["type"] == "SELL":
                    if cci_yesterday > cci_sma_yesterday and cci_now < cci_sma_now:
                        active_setup["entry_signal_index"] = i

            # 3️⃣ On the 3rd day: Confirm entry
            elif days_since_trigger == 3:
                if "entry_signal_index" in active_setup:
                    prior_candle = df.iloc[i-1]
                    if active_setup["type"] == "BUY":
                        if today["high"] > prior_candle["high"]:
                            trades.append({
                                "date": today.name,
                                "entry": prior_candle["high"],
                                "stop_loss": prior_candle["low"],
                                "signal": "BUY",
                                "strategy": "bollinger_cci"
                            })


                    elif active_setup["type"] == "SELL":
                        if today["low"] < prior_candle["low"]:
                            trades.append({
                                "date": today.name,
                                "entry": prior_candle["low"],
                                "stop_loss": prior_candle["high"],
                                "signal": "SELL",
                                "strategy": "bollinger_cci"
                            })
                # Setup expires whether or not entry happens
                active_setup = None

            # 4️⃣ Setup expires after 2 days without CCI cross
            elif days_since_trigger > 3:
                active_setup = None

    return trades