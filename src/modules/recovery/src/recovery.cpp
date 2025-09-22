#include "module_api.h"
#include "logger.h"
#include "recovery_mode.h"
#include "ee_engine.h"
#include <string>
#include "host_services_c.h"
#include <cstdlib>
#include <fstream>
#include <memory>

using namespace gscx;
using namespace gscx::recovery;

extern "C" __declspec(dllexport) ModuleInfo GSCX_GetModuleInfo() {
    return ModuleInfo{ .name = "recovery", .version_major = 1, .version_minor = 0 };
}

extern "C" void GSCX_RecoveryEntry();

static HostServicesC g_host{};
static std::unique_ptr<RecoveryMode> g_recovery_mode;
static std::unique_ptr<Bootloader> g_bootloader;
static std::unique_ptr<EmotionEngine> g_emotion_engine;

extern "C" __declspec(dllexport) bool GSCX_Initialize(void* host_ctx) {
    if (host_ctx) {
        g_host = *reinterpret_cast<HostServicesC*>(host_ctx);
        // Redirecionar Logger para callbacks do host
        Logger::set_info([](const char* m){ if (g_host.log_info) g_host.log_info(m); });
        Logger::set_warn([](const char* m){ if (g_host.log_warn) g_host.log_warn(m); });
        Logger::set_error([](const char* m){ if (g_host.log_error) g_host.log_error(m); });
    }
    
    // Initialize translation system
    I18n::set_language(Language::ENGLISH);
    
    // Create subsystems
    g_bootloader = std::make_unique<Bootloader>(&g_host);
    g_recovery_mode = std::make_unique<RecoveryMode>(&g_host);
    g_emotion_engine = std::make_unique<EmotionEngine>(&g_host);
    
    // Initialize bootloader
    if (!g_bootloader->initialize()) {
        Logger::error("Failed to initialize bootloader");
        return false;
    }
    
    // Initialize recovery mode
    if (!g_recovery_mode->initialize()) {
        Logger::error("Failed to initialize recovery mode");
        return false;
    }
    
    // Initialize Emotion Engine
    if (!g_emotion_engine->initialize()) {
        Logger::error("Failed to initialize Emotion Engine");
        return false;
    }
    
    Logger::info(I18n::t(keys::RECOVERY_INIT));
    return true;
}

// Recovery Mode API Functions
extern "C" __declspec(dllexport) void GSCX_PowerOn() {
    if (g_recovery_mode) {
        g_recovery_mode->power_on();
    }
}

extern "C" __declspec(dllexport) void GSCX_PowerOff() {
    if (g_recovery_mode) {
        g_recovery_mode->power_off();
    }
}

extern "C" __declspec(dllexport) void GSCX_EjectDisc() {
    if (g_recovery_mode) {
        g_recovery_mode->eject_disc();
    }
}

extern "C" __declspec(dllexport) bool GSCX_InsertDisc(const char* iso_path) {
    if (g_recovery_mode && iso_path) {
        g_recovery_mode->insert_disc(iso_path);
        return true;
    }
    return false;
}

extern "C" __declspec(dllexport) bool GSCX_LoadPUP(const char* pup_path) {
    if (g_recovery_mode && pup_path) {
        return g_recovery_mode->load_pup_file(pup_path);
    }
    return false;
}

extern "C" __declspec(dllexport) void GSCX_SetLanguage(int lang) {
    Language language = static_cast<Language>(lang);
    if (g_recovery_mode) {
        g_recovery_mode->set_language(language);
    }
}

extern "C" __declspec(dllexport) void GSCX_ShowRecoveryMenu() {
    if (g_recovery_mode) {
        g_recovery_mode->show_recovery_menu();
    }
}

extern "C" __declspec(dllexport) void GSCX_HandleMenuSelection(int selection) {
    if (g_recovery_mode) {
        g_recovery_mode->handle_menu_selection(selection);
    }
}

// Bootloader API Functions
extern "C" __declspec(dllexport) bool GSCX_BootRecoveryMode() {
    if (g_bootloader) {
        return g_bootloader->boot_recovery_mode();
    }
    return false;
}

extern "C" __declspec(dllexport) bool GSCX_BootSystemSoftware() {
    if (g_bootloader) {
        return g_bootloader->boot_system_software();
    }
    return false;
}

// Emotion Engine API Functions
extern "C" __declspec(dllexport) void GSCX_EE_ExecuteCycle() {
    if (g_emotion_engine) {
        g_emotion_engine->execute_cycle();
    }
}

extern "C" __declspec(dllexport) void GSCX_EE_Reset() {
    if (g_emotion_engine) {
        g_emotion_engine->reset();
    }
}

extern "C" __declspec(dllexport) uint64_t GSCX_EE_GetRegister(int reg) {
    if (g_emotion_engine) {
        return g_emotion_engine->get_gpr(reg);
    }
    return 0;
}

extern "C" __declspec(dllexport) void GSCX_EE_SetRegister(int reg, uint64_t value) {
    if (g_emotion_engine) {
        g_emotion_engine->set_gpr(reg, value);
    }
}

/**
 * @brief Main recovery mode entry point called from assembly
 * 
 * Assembly Integration:
 * - Called from recovery_entry.c after hardware initialization
 * - Assumes CPU is in protected mode with stack setup
 * - Hardware interrupts should be disabled during critical sections
 * - Memory management unit (MMU) must be configured
 * 
 * Boot Sequence:
 * 1. LV0: Initial hardware validation and security checks
 * 2. LV1: Hypervisor setup and memory mapping
 * 3. LV2: Recovery mode kernel initialization
 */
extern "C" void GSCX_RecoveryMain() {
    Logger::info("Recovery Main: Starting multi-stage boot sequence");
    
    try {
        // Stage 1: Validate bootloader state
        if (!g_bootloader) {
            Logger::error("Bootloader not initialized - cannot enter recovery mode");
            return;
        }
        
        // Stage 2: Execute recovery mode boot sequence
        Logger::info("Executing LV0/LV1/LV2 boot sequence for recovery mode");
        if (g_bootloader->boot_recovery_mode()) {
            Logger::info("Boot sequence completed successfully");
            
            // Stage 3: Start recovery mode main loop
            if (g_recovery_mode) {
                Logger::info("Starting recovery mode main loop");
                g_recovery_mode->run_main_loop();
                Logger::info("Recovery mode main loop completed");
            } else {
                Logger::error("Recovery mode instance not available");
            }
        } else {
            Logger::error("Boot sequence failed - hardware validation error");
        }
    } catch (const std::exception& e) {
        Logger::error("Recovery main exception: " + std::string(e.what()));
    } catch (...) {
        Logger::error("Unknown exception in recovery main");
    }
}

/**
 * @brief Shutdown recovery module with proper cleanup
 * 
 * Assembly Integration:
 * - Ensures all hardware resources are properly released
 * - Disables interrupts and restores original handlers
 * - Clears memory mappings and security contexts
 */
extern "C" __declspec(dllexport) void GSCX_Shutdown() {
    Logger::info("Recovery module: Starting shutdown sequence");
    
    try {
        // Shutdown subsystems in reverse order
        if (g_emotion_engine) {
            Logger::info("Shutting down Emotion Engine");
            g_emotion_engine.reset();
        }
        
        if (g_recovery_mode) {
            Logger::info("Shutting down Recovery Mode");
            g_recovery_mode.reset();
        }
        
        if (g_bootloader) {
            Logger::info("Shutting down Bootloader");
            g_bootloader.reset();
        }
        
        // Clear host services
        std::memset(&g_host, 0, sizeof(g_host));
        
        Logger::info("Recovery module: Shutdown completed successfully");
    } catch (const std::exception& e) {
        Logger::error("Shutdown exception: " + std::string(e.what()));
    } catch (...) {
        Logger::error("Unknown exception during shutdown");
    }
}