cmake_minimum_required(VERSION 3.15)
project(lsp-framework-test CXX)

find_package(lsp CONFIG REQUIRED)

add_executable(lsp-framework-test main.cpp)
target_link_libraries(lsp-framework-test PRIVATE lsp::liblsp)
set_property(TARGET lsp-framework-test PROPERTY CXX_STANDARD 20)