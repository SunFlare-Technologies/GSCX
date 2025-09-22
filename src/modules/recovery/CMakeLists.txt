add_library(gscx_recovery SHARED 
    src/recovery.cpp
    src/recovery_entry.c
    src/recovery_entry.asm
    src/recovery_i18n.cpp
    src/recovery_mode.cpp
    src/bootloader.cpp
    src/ee_engine.cpp
    src/ps3_models.cpp
    src/pup_reader.cpp
)

target_include_directories(gscx_recovery PUBLIC ../../core/include)

target_link_libraries(gscx_recovery PRIVATE gscx_core)

# Symbol is now exported via __declspec(dllexport) in C code

set_target_properties(gscx_recovery PROPERTIES OUTPUT_NAME "gscx_recovery")