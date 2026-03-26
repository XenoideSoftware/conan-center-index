cmake_minimum_required(VERSION 3.15)
project(lexilla-test CXX)

find_package(lexilla CONFIG REQUIRED)

add_executable(lexilla-test main.cpp)
target_link_libraries(lexilla-test PRIVATE lexilla)
