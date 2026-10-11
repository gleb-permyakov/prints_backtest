import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from binance.client import Client
from binance.exceptions import BinanceAPIException

SYMBOL = os.getenv("SYMBOL")
HOURS_BACK = int(os.getenv("HOURS_BACK"))
OUTPUT_TRADES = os.getenv("PATH_DATA") + "trades/" + SYMBOL + ".json"
OUTPUT_KLINES = os.getenv("PATH_DATA") + "klines/"

import json
import os
import time


def save_1s_klines_last_hour(client, output_path, symbol):
    """
    Забирает 1s свечи с фьючерсного рынка (USDT-M) за последний час
    и сохраняет в output_path/<symbol>.json
    """
    os.makedirs(output_path, exist_ok=True)

    # Текущее время в миллисекундах
    end_time = int(time.time() * 1000)
    start_time = end_time - 3600 * 1000 * HOURS_BACK # минимум n час

    all_candles = []
    cursor = start_time

    # Binance отдаёт максимум 1500 свечей за раз для futures,
    # но берём 900 с запасом — безопаснее
    batch_limit = 900

    while cursor < end_time:
        try:
            klines = client.futures_klines(
                symbol=symbol,
                interval="1m",
                startTime=cursor,
                endTime=end_time,
                limit=batch_limit,
            )
        except Exception as e:
            print(f"[Ошибка] Запрос не удался: {e}")
            break

        if not klines:
            break

        for k in klines:
            all_candles.append({
                "open_time": k[0],
                "open": k[1],
                "high": k[2],
                "low": k[3],
                "close": k[4],
                "volume": k[5],
                "close_time": k[6],
                "quote_volume": k[7],
                "trades": k[8],
                "taker_buy_base": k[9],
                "taker_buy_quote": k[10],
            })

        # Следующий запрос начинаем с close_time последней свечи + 1 мс
        last_close_time = klines[-1][6]
        cursor = last_close_time + 1

        print(f"[Прогресс] Уже загружено {len(all_candles)} свечей")
        time.sleep(0.3)  # защита от лимитов API

    # Убираем дубликаты по open_time
    seen = set()
    unique_candles = []
    for c in all_candles:
        if c["open_time"] not in seen:
            seen.add(c["open_time"])
            unique_candles.append(c)

    # Сортируем по времени
    unique_candles.sort(key=lambda x: x["open_time"])

    # Сохраняем в файл
    filename = os.path.join(output_path, f"{symbol}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(unique_candles, f, indent=2, ensure_ascii=False)

    print(f"[Готово] Сохранено {len(unique_candles)} свечей в {filename}")
    return unique_candles


def get_futures_trades(client, symbol, hours_back):
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours_back)
    start_ts = int(start_time.timestamp() * 1000)
    end_ts = int(end_time.timestamp() * 1000)

    print(f"Сбор трейдов {symbol}: {start_time} .. {end_time}")

    all_trades = []
    current_start = start_ts
    limit = 1000  # максимум для futures_agg_trades

    while current_start < end_ts:
        try:
            data = client.futures_aggregate_trades(
                symbol=symbol,
                startTime=current_start,
                endTime=end_ts,
                limit=limit,
            )
        except BinanceAPIException as e:
            print(f"Ошибка Binance API: code={e.code} msg={e.message}")
            break
        except Exception as e:
            print(f"Ошибка запроса: {e}")
            break

        if not data:
            break

        all_trades.extend(data)

        # Если вернулось меньше лимита — данные кончились
        if len(data) < limit:
            break

        # Сдвигаем окно вперёд от последнего полученного трейда
        last_time = data[-1]["T"]
        if last_time <= current_start:
            break
        current_start = last_time + 1

        time.sleep(0.4)

    # Дедуп по id агрегированного трейда, сортировка по времени
    unique = {t["a"]: t for t in all_trades}
    result = sorted(unique.values(), key=lambda x: x["T"])
    print(f"Собрано уникальных трейдов: {len(result)}")
    return result


def save_to_json(data, filepath):
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Сохранено в {filepath}: {len(data)} записей")


def main():
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        raise SystemExit("Не заданы BINANCE_API_KEY / BINANCE_API_SECRET.")

    client = Client(api_key.strip(), api_secret.strip(), testnet=False)
    client.session.headers.update({"User-Agent": "python-binance"})

    try:
        client.futures_ping()
        print("Подключение к Binance Futures API: OK")
    except Exception as e:
        raise SystemExit(f"Не удалось подключиться к Binance: {e}")

    save_1s_klines_last_hour(client, output_path=OUTPUT_KLINES, symbol=SYMBOL)

    trades = get_futures_trades(client, SYMBOL, HOURS_BACK)
    if not trades:
        print("Трейды не найдены.")
        return

    save_to_json(trades, OUTPUT_TRADES)

    # first = datetime.fromtimestamp(trades[0]["T"] / 1000, tz=timezone.utc)
    # last = datetime.fromtimestamp(trades[-1]["T"] / 1000, tz=timezone.utc)
    # print(f"Первый трейд: {first}")
    # print(f"Последний трейд: {last}")


if __name__ == "__main__":
    main()