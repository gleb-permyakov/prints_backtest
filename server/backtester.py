import json
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

SYMBOL = os.getenv("SYMBOL")
OUTPUT_FILE = os.getenv("PATH_DATA") + SYMBOL + ".json"

with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

def s_to_ms(s): return s*1000

class Position:
    """
    side: -1, 0, 1
    qty: объем в монетах
    """
    def __init__(self, side, qty):
        self.side = side
        self.qty = qty

class Win:
    """
    arr: массив трейдов
    time_span: за какой период времени (в секундах)
    """
    def __init__(self, arr, time_span): 
        self.arr = arr 
        self.time_span = time_span

W_1 = os.getenv("W_1"), W_2 = os.getenv("W_2")
win_1 = Win([], W_1)
win_2 = Win([], W_2)

START_T_1 = data[0]["T"]
END_T = data[0]["T"] + s_to_ms(W_1)
START_T_2 = END_T - s_to_ms(W_2)

def win_editor(win: Win):
    time_span = s_to_ms(win.time_span)
    if len(win.arr) > 0:
        return 0
        # for i in win:
    else:
        new_trades = []
        for trade in data:
            trade_time = trade["T"]
            if trade_time >= (END_T - win.time_span) and trade_time <= END_T:
                new_trades.append(trade)
        win.arr.extend(new_trades)



win_editor(win_1, W_1)
win_editor(win_2, W_2)


# while True:
#     win_1 = []
#     win_2 = []
#     for i in 






