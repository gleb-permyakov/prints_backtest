#pragma once
#include <vector>
#include <string>

struct Trade {
	int64_t a = 0;
	double  p = 0.0;
	double  q = 0.0;
	double  nq = 0.0;
	int64_t f = 0;
	int64_t l = 0;
	int64_t T = 0;
	bool    m = false;
};

struct Position {
	// status: -1, 0, 1
	// qty : объем в $
	// price_in : цена входа в сделку
	// price_out : цена выхода из сделки
	// time_in : время входа в сделку
	// time_out : время выхода из сделки
	// reason_out : причина выхода из сделки
	// pnl : результат в деньгах
	// pct : процент движения
	int status = 0;
	double qty = 0;
	double price_in = 0;
	double price_out = 0;
	int64_t time_in = 0;
	int64_t time_out = 0;
	std::string reason_out = "";
	double pnl = 0;
	double pct = 0;
};

struct Win {
	// arr : массив трейдов
	// time_span : за какой период времени(в секундах)
	// i0 : индекс левой границы окна
	// i1 : индекс правой границы окна
	std::vector<Trade>* arr = nullptr;
	int64_t time_span = 0;
	size_t i0 = 0;
	size_t i1 = 0;
};