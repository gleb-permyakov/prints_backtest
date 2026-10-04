#include <iostream>
#include <fstream>
#include <vector>
#include <string>
#include <cstdint>
#include <stdexcept>
#include <clocale>
#include <iomanip>

#include "lib.h"
#include "types.h"

#include "json.hpp"
using json = nlohmann::json;

int64_t W_1 = 60;
int64_t W_2 = 10;

static std::string read_file(const std::string& path) {
	std::ifstream f(path, std::ios::binary);
	if (!f) throw std::runtime_error("Не могу открыть файл: " + path);
	f.seekg(0, std::ios::end);
	std::streamsize size = f.tellg();
	f.seekg(0, std::ios::beg);
	if (size < 0) throw std::runtime_error("Не могу определить размер: " + path);
	std::string buf;
	if (size > 0) {
		buf.resize(static_cast<size_t>(size));
		f.read(&buf[0], size);
	}
	return buf;
}

static double get_double(const json& j, const char* key) {
	if (!j.contains(key)) return 0.0;
	const auto& v = j.at(key);
	if (v.is_number()) return v.get<double>();
	if (v.is_string()) return std::stod(v.get<std::string>());
	return 0.0;
}

static int64_t get_int64(const json& j, const char* key) {
	if (!j.contains(key)) return 0;
	const auto& v = j.at(key);
	if (v.is_number_integer()) return v.get<int64_t>();
	if (v.is_number())         return static_cast<int64_t>(v.get<double>());
	if (v.is_string())         return std::stoll(v.get<std::string>());
	return 0;
}

static bool get_bool(const json& j, const char* key) {
	if (!j.contains(key)) return false;
	const auto& v = j.at(key);
	if (v.is_boolean()) return v.get<bool>();
	if (v.is_string())  return v.get<std::string>() == "true";
	if (v.is_number())  return v.get<double>() != 0.0;
	return false;
}

static int64_t s_to_ms(double s) {
	return s * 1000;
}

// функция заполнения окон
//void win_editor(Win& win, int64_t END_T) {
//	int64_t time_span = win.time_span;
//	size_t n = win.arr->size();
//
//	while (win.i0 < n && (*win.arr)[win.i0].T <= END_T - time_span) {
//		++win.i0;
//	}
//	while (win.i1 < n && (*win.arr)[win.i1].T <= END_T) {
//		++win.i1;
//	}
//}

int win_editor(Win& win, int64_t& END_T) {
	int64_t time_span = s_to_ms(win.time_span);

	// если уже есть заполненное окно
	if (win.i1 > 0) {
		// корректировка левой границы
		for (size_t i = win.i0; i < win.arr->size(); ++i) {
			int64_t trade_time = (*win.arr)[i].T;
			if (trade_time <= END_T - time_span) {
				win.i0 += 1;
			}
			else {
				break;
			}
		}
		// корректировка правой границы
		for (size_t i = win.i1; i < win.arr->size(); ++i) {
			int64_t trade_time = (*win.arr)[i].T;
			if (trade_time <= END_T) {
				win.i1 += 1;
			}
			else {
				break;
			}
		}
	}
	// первое заполнение окна
	else {
		for (size_t i = 0; i < win.arr->size(); ++i) {
			int64_t trade_time = (*win.arr)[i].T;
			if (trade_time <= END_T - time_span) {
				win.i0 += 1;
			}
			if (trade_time <= END_T) {
				win.i1 += 1;
			}
			else {
				break;
			}
		}
	}
	return 0;
}

int main() {
	//setlocale(LC_ALL, "Russian");
	try {
		const std::string path = "../../../data/ONEUSDT.json";
		const std::string text = read_file(path);
		json j = json::parse(text);

		if (!j.is_array())
			throw std::runtime_error("Ожидался JSON-массив в " + path);

		std::vector<Trade> trades;
		trades.reserve(j.size());

		for (const auto& item : j) {
			Trade t;
			t.a = get_int64(item, "a");
			t.p = get_double(item, "p");
			t.q = get_double(item, "q");
			t.nq = get_double(item, "nq");
			t.f = get_int64(item, "f");
			t.l = get_int64(item, "l");
			t.T = get_int64(item, "T");
			t.m = get_bool(item, "m");
			trades.push_back(t);
		}

		std::cout << "Got trades: " << trades.size() << "\n";
		/*std::cout << "Первые 5:\n";
		for (size_t i = 0; i < trades.size() && i < 5; ++i) {
			const auto& t = trades[i];
			std::cout << "  T=" << t.T
				<< "  p=" << t.p
				<< "  q=" << t.q
				<< "  nq=" << t.nq
				<< "  m=" << (t.m ? "true" : "false")
				<< "\n";
		}*/

		// win init
		Win win_1, win_2;
		win_1.arr = &trades;
		win_1.time_span = W_1;
		win_2.arr = &trades;
		win_2.time_span = W_2;

		// инициализация таймингов пересчета
		int64_t START_T = trades[0].T;
		int64_t END_T = START_T + s_to_ms(W_1);

		// инициализация позиции и истории позиций
		Position position;
		std::vector<Position> history;

		// цикл обработки
		while (true) {
			win_editor(win_1, END_T);
			win_editor(win_2, END_T);
			check_position(win_1, win_2, position);

			if (!position.reason_out.empty()) {          // "" → .empty()
				history.push_back(position);             // просто копируем в вектор
				position = Position();                   // сброс
			}

			END_T += s_to_ms(0.5);
			/*if ((END_T - START_T) % 500000 == 0) {
				std::cout << ((END_T - START_T) / 1000) << " s passed\n";
			}*/

			if (trades.back().T < END_T) {
				std::cout << "\n\nREADY!\n";
				std::cout << "+-----+--------+----------+-----------+-----------+----------+----------+\n";
				std::cout << "|  #  | status |   qty    | price_in  | price_out |   pnl    |   pct    |\n";
				std::cout << "+-----+--------+----------+-----------+-----------+----------+----------+\n";

				for (size_t i = 0; i < history.size(); ++i) {
					const Position& p = history[i];
					std::cout << "| " << std::setw(3) << i
						<< " | " << std::setw(6) << p.status
						<< " | " << std::setw(8) << std::fixed << std::setprecision(2) << p.qty
						<< " | " << std::setw(9) << p.price_in
						<< " | " << std::setw(9) << p.price_out
						<< " | " << std::setw(8) << p.pnl
						<< " | " << std::setw(8) << p.pct
						<< " |\n";
				}

				std::cout << "+-----+--------+----------+-----------+-----------+----------+----------+\n";
				std::cout << "Positions: " << history.size() << "\n";

				break;
			}
		}
			

	}
	catch (const std::exception& e) {
		std::cerr << "Ошибка: " << e.what() << "\n";
		return 1;
	}

	return 0;
}

