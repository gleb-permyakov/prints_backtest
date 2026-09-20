import json
import copy
import os
from pathlib import Path

from finder import Check_position

# ИМПОРТЫ ДЛЯ ПОСТРОЕНИЯ ГРАФИКА
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# ENVIRONMENT
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

SYMBOL = os.getenv("SYMBOL")
OUTPUT_FILE = os.getenv("PATH_DATA") + SYMBOL + ".json"
W_1 = float(os.getenv("W_1"))
W_2 = float(os.getenv("W_2"))
DELTA_TIME = float(os.getenv("DELTA_TIME"))
index_first_trade = 0

# data - все трейды gj bycnhevtyne
with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# seconds to milliseconds
def s_to_ms(s): return float(s)*1000

class Position:
    """
    side: -1, 0, 1
    qty: объем в монетах
    price_in: цена входа в сделку
    price_out: цена выхода из сделки
    time_in: время входа в сделку
    time_out: время выхода из сделки
    reason: причина выхода из сделки
    pnl: результат в деньгах
    pct: процент движения
    """
    def __init__(self):
        self.status = 0
        self.qty = 0
        self.price_in = 0
        self.price_out = 0
        self.time_in = 0
        self.time_out = 0
        self.reason_out = ""
        self.pnl = 0
        self.pct = 0


class Win:
    """
    arr: массив трейдов
    time_span: за какой период времени (в секундах)
    """
    def __init__(self, arr, time_span): 
        self.arr = arr 
        self.time_span = time_span
        self.i0 = 0
        self.i1 = 0
    def set_i0(self, i0): 
        self.i0 = i0
    def set_i1(self, i1): 
        self.i1 = i1


win_1 = Win(data, W_1)
win_2 = Win(data, W_2)

START_T = data[0]["T"] 
END_T = data[0]["T"] + s_to_ms(W_1)

def win_editor(win: Win):
    time_span = s_to_ms(win.time_span)
    if win.i1 > 0:
        # заполнение окошек
        win.i1 = win.i0
        for trade in data[win.i0:]:
            trade_time = trade["T"]
            if trade_time <= END_T - time_span:
                win.i0 += 1
            if trade_time <= END_T:
                win.i1 += 1
            else: break
    else:
        # заполнение окошек
        for trade in data:
            trade_time = trade["T"]
            if trade_time <= END_T - time_span:
                win.i0 += 1
            if trade_time <= END_T:
                win.i1 += 1
            else: break

position = Position()
history = []

while True:
    win_editor(win_1)
    win_editor(win_2)
    Check_position(win_1.arr[win_1.i0:win_1.i1], win_2.arr[win_2.i0:win_2.i1], position)
    if position.reason_out != "":
        history.append(copy.deepcopy(position))
        print(position)
        position = Position()

    END_T += s_to_ms(DELTA_TIME)
    # if (END_T - START_T) % 10000 == 0:
    #     print((END_T - START_T) / 1000, "s passed")

    if data[-1]['T'] < END_T:
        for i in history:
            print(i.status, i.pnl, i.pct, "\n")

        df = pd.DataFrame([vars(p) for p in history])
        # время в datetime
        df["time_out_dt"] = pd.to_datetime(df["time_out"], unit="ms")
        df["time_in_dt"]  = pd.to_datetime(df["time_in"],  unit="ms")

        START_CAPITAL = 10   # поставьте своё

        df["equity"]   = START_CAPITAL + df["pnl"].cumsum()
        df["peak"]     = df["equity"].cummax()
        df["dd"]       = df["equity"] - df["peak"]
        df["dd_pct"]   = df["dd"] / df["peak"] * 100

        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(14, 8), sharex=True,
            gridspec_kw={"height_ratios": [3, 1]}
        )

        # ---- equity ----
        ax1.plot(df["time_out_dt"], df["equity"],
                color="tab:blue", lw=1.5, label="Equity")
        ax1.axhline(START_CAPITAL, color="gray", ls="--", lw=0.8)
        ax1.set_ylabel("Equity, $")
        ax1.set_title("Equity curve")
        ax1.grid(alpha=0.3)
        ax1.legend(loc="upper left")

        # ---- drawdown ----
        ax2.fill_between(df["time_out_dt"], df["dd_pct"], 0,
                        color="tab:red", alpha=0.4)
        ax2.set_ylabel("Drawdown, %")
        ax2.set_xlabel("Время")
        ax2.grid(alpha=0.3)

        # формат дат на оси X
        ax2.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M"))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=30, ha="right")

        plt.tight_layout()
        plt.show()

        break
