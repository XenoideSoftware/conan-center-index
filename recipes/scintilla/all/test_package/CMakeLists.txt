cmake_minimum_required(VERSION 3.15)
project(scintillaTest CXX)

set(CMAKE_AUTOMOC ON)

find_package(Qt6 REQUIRED COMPONENTS Core)
find_package(scintilla CONFIG REQUIRED)

add_executable(scintillaTest main.cpp)
target_link_libraries(scintillaTest PRIVATE scintilla Qt6::Core)
