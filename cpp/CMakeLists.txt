cmake_minimum_required(VERSION 3.16)
project(edge_adapter LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(edge_adapter src/edge_adapter.cpp)
