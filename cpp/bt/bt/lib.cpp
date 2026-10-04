#include "lib.h"
#include "types.h"
#include <iostream>
#include <vector>

int after_dot = 2; // точность цены(цифр после точки)
double koeff = 1.15; // коэффициент перевеса

double max(double a, double b) {
	if (a > b) { return a; }
	return b;
}

double min(double a, double b) {
	if (a < b) { return a; }
	return b;
}

void check_position(Win& win_1, Win& win_2, Position& position) {
	// проверка большого окна
	int trend = 1;
	if (!win_1.arr->empty()) {
		double trend_long = 0;
		double trend_short = 0;
		// локальная ссылка для удобства
		std::vector<Trade>& arr = *win_1.arr;
		// перебор элементов окна
		for (size_t i = win_1.i0; i < win_1.i1; ++i) {
			Trade& trade = arr[i];
			double quantity = trade.q;
			if (trade.m == true) {
				trend_short += quantity;
			}
			else {
				trend_long += quantity;
			}
			//std::cout << trade.p << " " << trade.q << "\n";
		}
		//std::cout << win_1.i0 << " " << win_1.i1 << " " << trend_long << " " << trend_short << "\n";
		// определение направления главного тренда
		if (trend_long / trend_short >= 1.15) { trend = 2; }
		else if (trend_long / trend_short >= 1.05 and trend_long / trend_short < 1.2) { trend = 1; }
		else if (trend_short / trend_long >= 1.15) { trend = -2; }
		else if (trend_short / trend_long >= 1.05 and trend_short / trend_long < 1.2) { trend = -1; }
	}
	else {
		return;
	}
	// проверка малого окна
	double long_volume = 0;
	double short_volume = 0;
	double middle_long = 0;
	double middle_short = 0;
	if (!win_2.arr->empty()) {
		// локальная ссылка для удобства
		std::vector<Trade>& arr = *win_2.arr;
		// перебор элементов
		for (size_t i = win_2.i0; i < win_2.i1; ++ i) {
			Trade& trade = arr[i];
			// подсчет объемов
			int side = 1;
			if (trade.m == true) { side = -1; }
			double quantity = trade.q;
			double price = trade.p;
			if (long_volume != 0 and short_volume != 0) {
				if (side == 1) {
					if (long_volume + quantity != 0) {
						middle_long = middle_long * long_volume / (long_volume + quantity) + quantity * price * side / (long_volume + quantity);
					}
				}
				else if (side == -1) {
					if (short_volume + quantity != 0) {
						middle_short = middle_short * short_volume / (short_volume + quantity) + quantity * price / (short_volume + quantity);
					}
				}
			}
			else {
				if (side == 1 && quantity != 0) {
					middle_long = (quantity * price) / quantity;
				}
				else if (side == -1 && quantity != 0) {
					middle_short = (quantity * price) / quantity;
				}
			}
			if (side == 1) {
				long_volume += quantity;
			}
			else {
				short_volume += quantity;
			}
		}
	}
	else {
		return;
	}
	// подсчет перевеса объема
	bool volume_disbalance = max(long_volume, short_volume) / min(long_volume, short_volume) >= koeff;
	// актуальная цена
	double actual_price = (*win_1.arr)[win_1.i1].p;
	// подсчет разницы уровней покупки и продаж
	double l_diff = 0;
	double s_diff = 0;
	if (actual_price != 0) {
		l_diff = std::round((middle_long / actual_price - 1) * 10000.0) / 100.0;
		s_diff = std::round((middle_short / actual_price - 1) * 10000.0) / 100.0;
	}
	//std::cout << middle_long << "\n";
	//std::cout << actual_price << middle_long << l_diff << s_diff << short_volume << volume_disbalance << trend << "\n";
	// вход в сделку
	if (position.status == 0) {
		if (actual_price < middle_long and actual_price < middle_short and l_diff > 0.05 and l_diff < 0.15 and long_volume > short_volume and volume_disbalance and trend == 2) {
			position.status = 1;
			position.price_in = actual_price;
			position.qty = 100;
			position.time_in = (*win_1.arr)[win_1.i1].T;
		}
		else if (actual_price > middle_long and actual_price > middle_short and s_diff < -0.05 and s_diff > -0.15 and long_volume < short_volume and volume_disbalance and trend == -2) {
			position.status = -1;
			position.price_in = actual_price;
			position.qty = 100;
			position.time_in = (*win_1.arr)[win_1.i1].T;
		}
	}
	// условия выхода из лонга
	else if (position.status == 1 && (trend == -1 || trend == -2)) {
		position.price_out = actual_price;
		position.time_out = (*win_1.arr)[win_1.i1].T;
		position.reason_out = "main trand out";
		position.pct = position.price_out / position.price_in - 1;
		position.pnl = position.pct * position.qty - 0.001 * position.qty;
	}
	// условия выхода из шорта
	else if (position.status == -1 && (trend == 1 || trend == 2)) {
		position.price_out = actual_price;
		position.time_out = (*win_1.arr)[win_1.i1].T;
		position.reason_out = "main trand out";
		position.pct = 1 - position.price_out / position.price_in;
		position.pnl = position.pct * position.qty - 0.001 * position.qty;
	}
}
