import json
import copy
import os
from pathlib import Path

from datetime import datetime

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
    status: -1, 0, 1
    qty: объем в монетах
    price_in: цена входа в сделку
    price_out: цена выхода из сделки
    time_in: время входа в сделку
    time_out: время выхода из сделки
    reason_out: причина выхода из сделки
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
            else: break
        for trade in data[win.i1:]:
            trade_time = trade["T"]
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
        history.append({
            "entryTime": position.time_in,
            "entryPrice": position.price_in,
            "exitTime": position.time_out,
            "exitPrice": position.price_out,
            "pnl": position.pnl,
            # дополнительные поля (не обязательны для графика, но полезны)
            "status": position.status,
            "qty": position.qty,
            "reason": position.reason_out,
            "pct": position.pct,
        })
        position = Position()

    END_T += s_to_ms(DELTA_TIME)
    if (END_T - START_T) % 10000 == 0:
        print((END_T - START_T) / 1000, "s passed")

    if data[-1]['T'] < END_T:
        for i in history:
            print(i["status"], i["pnl"], i["pct"], "\n")

        # json_array = [position_to_dict(p) for p in history]
        json_array = history

        with open("../data/positions.json", "w", encoding="utf-8") as f:
            json.dump(json_array, f, ensure_ascii=False, indent=2)

        # 2. DataFrame прямо из списка словарей
        df = pd.DataFrame(history)

        # 3. Время в datetime (колонки называются как в словаре!)
        df["exit_dt"] = pd.to_datetime(df["exitTime"], unit="ms")
        df["entry_dt"] = pd.to_datetime(df["entryTime"], unit="ms")

        # 4. Кривая капитала
        START_CAPITAL = 10
        df["equity"] = START_CAPITAL + df["pnl"].cumsum()
        df["peak"]   = df["equity"].cummax()
        df["dd"]     = df["equity"] - df["peak"]
        df["dd_pct"] = df["dd"] / df["peak"] * 100

        # 5. График
        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(14, 8), sharex=True,
            gridspec_kw={"height_ratios": [3, 1]}
        )

        # ---- Equity ----
        ax1.plot(df["exit_dt"], df["equity"],
                color="tab:blue", lw=1.5, label="Equity")
        ax1.axhline(START_CAPITAL, color="gray", ls="--", lw=0.8)
        ax1.set_ylabel("Equity, $")
        ax1.set_title("Equity curve")
        ax1.grid(alpha=0.3)
        ax1.legend(loc="upper left")

        # ---- Просадка ----
        ax2.fill_between(df["exit_dt"], df["dd_pct"], 0,
                        color="tab:red", alpha=0.4, label="Drawdown %")
        ax2.set_ylabel("Drawdown, %")
        ax2.set_xlabel("Time")
        ax2.grid(alpha=0.3)
        ax2.legend(loc="lower left")

        plt.tight_layout()
        plt.savefig("../data/equity.png", dpi=120)
        plt.show()

        break

# Или просто получаем строку
# json_str = json.dumps(json_array, ensure_ascii=False, indent=2)
# print(json_str)
