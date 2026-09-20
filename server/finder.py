# from backtester import Win, Position

after_dot = 2 # точность цены (цифр после точки)
koeff = 1.15 # коэффициент перевеса

# Проверка позиции
def Check_position(win_1, win_2, position):
    # Проверка большого окна
    trand = 0
    if win_1:
        trand_long = 0
        trand_short = 0
        for trade in win_1:
            side = 1
            if trade['m'] == True: side = -1
            quantity = float(trade['q'])
            if trade['m'] is False:
                trand_long += float(trade['q'])
            else:
                trand_short += float(trade['q'])
            # all_sum += quantity*side
        if trand_long/trand_short >= 1.15: trand = 2
        elif trand_long/trand_short >= 1.05 and trand_long/trand_short < 1.2: trand = 1
        elif trand_short/trand_long >= 1.15: trand = -2
        elif trand_short/trand_long >= 1.05 and trand_short/trand_long < 1.2: trand = -1 
    # Проверка малого окна
    long_volume = 0
    short_volume = 0
    middle_long = 0
    middle_short = 0
    if win_2:
        all_sum = 0
        for trade in win_2:
            side = 1
            if trade['m'] == True: side = -1
            quantity = float(trade['q'])
            price = float(trade['p'])
            if long_volume != 0 and short_volume != 0:
                if side == 1:
                    if (long_volume + quantity*side) == 0: middle_long = middle_long
                    else: middle_long = middle_long * long_volume/(long_volume + quantity*side) + quantity*price*side/(long_volume + quantity*side) 
                elif side == -1:
                    if (short_volume + quantity) == 0: middle_short = middle_short
                    else: middle_short = middle_short * short_volume/(short_volume + quantity) + quantity*price/(short_volume + quantity) 
            else:
                if side == 1:
                    if quantity == 0: middle_long = middle_long
                    else: middle_long = (quantity*price)/quantity
                elif side == -1:
                    if quantity == 0: middle_short = middle_short
                    else: middle_short = (quantity*price)/quantity
            if trade['m'] is False:
                long_volume += float(trade['q'])
            else:
                short_volume += float(trade['q'])
            all_sum += quantity*side
    # Подсчет перевеса объема
    volume_disbalance = max(long_volume, short_volume) / min(long_volume, short_volume) >= koeff
    # Актулаьная цена
    actual_price = float(win_1[-1]['p'])
    # Подсчет разницы уровней покупки и продаж
    l_diff = 0
    s_diff = 0
    if actual_price != 0:
        l_diff = round(middle_long / actual_price - 1, 4)*100
        s_diff = round(middle_short / actual_price - 1, 4)*100
    # Вход в сделку
    if position.status == 0:
        if actual_price < middle_long and actual_price < middle_short and l_diff > 0.05 and l_diff < 0.15 and long_volume > short_volume and volume_disbalance and trand == 2:
            position.status = 1
        elif actual_price > middle_long and actual_price > middle_short and s_diff < -0.05 and s_diff > -0.15 and long_volume < short_volume and volume_disbalance and trand == -2:
            position.status = -1
        position.price_in = actual_price
        position.qty = 100
        position.time_in = win_1[-1]["T"]
    # условия выхода из лонга
    elif position.status == 1:
        if trand == -1 or trand == -2:
            position.price_out = actual_price
            position.time_out = win_1[-1]["T"]
            position.reason_out = "main trand out"
            position.pct = position.price_out/position.price_in-1
            position.pnl = position.pct * position.qty - 0.001*position.qty
    # условия выхода из шорта  
    elif position.status == -1:
        if trand == 1 or trand == 2:
            position.price_out = actual_price
            position.time_out = win_1[-1]["T"]
            position.reason_out = "main trand out"
            position.pct = 1-position.price_out/position.price_in
            position.pnl = position.pct * position.qty - 0.001*position.qty
    # elif position.status == 1
    