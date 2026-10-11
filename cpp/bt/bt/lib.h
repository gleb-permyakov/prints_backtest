#pragma once
#include "types.h"
void check_position(Win& win_1, Win& win_2, Position& position);
bool save_positions(const std::string& path, const std::vector<Position>& positions);