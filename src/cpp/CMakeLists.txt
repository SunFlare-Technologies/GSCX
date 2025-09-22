# GSCX C++ supplemental library (utilities + C API)

add_library(gscx_cpp STATIC
    src/cpp_utils.cpp
    src/bindings_c.cpp
)

target_include_directories(gscx_cpp
    PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include
)

set_target_properties(gscx_cpp PROPERTIES
    CXX_STANDARD 20
    CXX_STANDARD_REQUIRED ON
)