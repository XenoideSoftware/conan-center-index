cmake_minimum_required(VERSION 3.25)
project(lexilla CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(scintilla REQUIRED)

# LEXILLA_SOURCES is passed in from the Conan generate() step
set(LEXILLA_SOURCES "${LEXILLA_SOURCES}" CACHE STRING "Lexilla source files")

# Convert semicolon-separated list to a proper CMake list
string(REPLACE ";" ";" LEXILLA_SOURCE_LIST "${LEXILLA_SOURCES}")

add_library(lexilla STATIC ${LEXILLA_SOURCE_LIST})

target_include_directories(lexilla PUBLIC
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/lexlib
    ${CMAKE_SOURCE_DIR}/src
)

target_link_libraries(lexilla PRIVATE scintilla)

install(TARGETS lexilla
    ARCHIVE DESTINATION lib
    LIBRARY DESTINATION lib
    RUNTIME DESTINATION bin
)
