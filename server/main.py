import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent / ".env")

from binance.client import Client
from binance.exceptions import BinanceAPIException

SYMBOL = "ONEUSDT"
HOURS_BACK = 1
OUTPUT_FILE = "data/oneusdt.json"


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

    trades = get_futures_trades(client, SYMBOL, HOURS_BACK)
    if not trades:
        print("Трейды не найдены.")
        return

    save_to_json(trades, OUTPUT_FILE)

    first = datetime.fromtimestamp(trades[0]["T"] / 1000, tz=timezone.utc)
    last = datetime.fromtimestamp(trades[-1]["T"] / 1000, tz=timezone.utc)
    print(f"Первый трейд: {first}")
    print(f"Последний трейд: {last}")


if __name__ == "__main__":
    main()