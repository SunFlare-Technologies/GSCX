/**
 * GSCX - PlayStation 3 High-Level Emulator
 * Hypervisor Implementation
 * 
 * This file implements the PS3 Hypervisor (HV) functionality
 * responsible for managing system resources, security, and
 * virtualization of the PlayStation 3 system.
 */

#include "../include/hypervisor.h"
#include "../include/logger.h"
#include <cstring>
#include <memory>
#include <vector>
#include <map>

namespace GSCX {
namespace Core {

// PS3 Hypervisor Constants
static const uint64_t HV_BASE_ADDR = 0x8000000000000000ULL;
static const uint64_t HV_SIZE = 0x1000000ULL; // 16MB
static const uint32_t HV_VERSION = 0x00030041; // PS3 HV version

// LPAR (Logical Partition) Management
struct LPAR {
    uint32_t id;
    uint64_t base_addr;
    uint64_t size;
    uint32_t privileges;
    bool active;
};

// Hypervisor State
static std::map<uint32_t, LPAR> lpars;
static uint32_t next_lpar_id = 1;
static bool hv_initialized = false;

Hypervisor::Hypervisor() {
    logger = std::make_unique<Logger>("Hypervisor");
    memory_manager = std::make_unique<HVMemoryManager>();
    security_manager = std::make_unique<HVSecurityManager>();
    
    // Initialize hypervisor subsystems
    initialize();
}

Hypervisor::~Hypervisor() {
    shutdown();
}

bool Hypervisor::initialize() {
    if (hv_initialized) {
        logger->warn("Hypervisor already initialized");
        return true;
    }
    
    logger->info("Initializing PS3 Hypervisor v%08X", HV_VERSION);
    
    // Initialize memory management
    if (!memory_manager->initialize(HV_BASE_ADDR, HV_SIZE)) {
        logger->error("Failed to initialize HV memory manager");
        return false;
    }
    
    // Initialize security subsystem
    if (!security_manager->initialize()) {
        logger->error("Failed to initialize HV security manager");
        return false;
    }
    
    // Create default LPAR for GameOS
    create_default_lpar();
    
    hv_initialized = true;
    logger->info("Hypervisor initialization complete");
    return true;
}

void Hypervisor::shutdown() {
    if (!hv_initialized) return;
    
    logger->info("Shutting down Hypervisor");
    
    // Destroy all LPARs
    for (auto& pair : lpars) {
        destroy_lpar(pair.first);
    }
    lpars.clear();
    
    // Shutdown subsystems
    security_manager->shutdown();
    memory_manager->shutdown();
    
    hv_initialized = false;
    logger->info("Hypervisor shutdown complete");
}

uint32_t Hypervisor::create_lpar(uint64_t size, uint32_t privileges) {
    if (!hv_initialized) {
        logger->error("Hypervisor not initialized");
        return 0;
    }
    
    uint32_t lpar_id = next_lpar_id++;
    
    // Allocate memory for LPAR
    uint64_t base_addr = memory_manager->allocate_lpar_memory(size);
    if (base_addr == 0) {
        logger->error("Failed to allocate memory for LPAR %u", lpar_id);
        return 0;
    }
    
    // Create LPAR structure
    LPAR lpar = {
        .id = lpar_id,
        .base_addr = base_addr,
        .size = size,
        .privileges = privileges,
        .active = true
    };
    
    lpars[lpar_id] = lpar;
    
    logger->info("Created LPAR %u: base=0x%016llX, size=0x%016llX, priv=0x%08X", 
                 lpar_id, base_addr, size, privileges);
    
    return lpar_id;
}

bool Hypervisor::destroy_lpar(uint32_t lpar_id) {
    auto it = lpars.find(lpar_id);
    if (it == lpars.end()) {
        logger->error("LPAR %u not found", lpar_id);
        return false;
    }
    
    LPAR& lpar = it->second;
    
    // Free LPAR memory
    memory_manager->free_lpar_memory(lpar.base_addr, lpar.size);
    
    // Remove from map
    lpars.erase(it);
    
    logger->info("Destroyed LPAR %u", lpar_id);
    return true;
}

bool Hypervisor::handle_hvcall(uint32_t opcode, uint64_t* args, uint64_t* result) {
    if (!hv_initialized) {
        logger->error("Hypervisor not initialized for hvcall");
        return false;
    }
    
    logger->debug("HV Call: opcode=0x%08X", opcode);
    
    switch (opcode) {
        case 0x1000: // HV_GET_VERSION
            *result = HV_VERSION;
            return true;
            
        case 0x1001: // HV_CREATE_LPAR
            *result = create_lpar(args[0], static_cast<uint32_t>(args[1]));
            return *result != 0;
            
        case 0x1002: // HV_DESTROY_LPAR
            *result = destroy_lpar(static_cast<uint32_t>(args[0])) ? 0 : -1;
            return true;
            
        case 0x2000: // HV_MEMORY_MAP
            return handle_memory_map(args, result);
            
        case 0x2001: // HV_MEMORY_UNMAP
            return handle_memory_unmap(args, result);
            
        case 0x3000: // HV_SECURITY_CHECK
            return security_manager->check_privileges(static_cast<uint32_t>(args[0]), args[1]);
            
        default:
            logger->warn("Unknown HV call: 0x%08X", opcode);
            *result = -1;
            return false;
    }
}

void Hypervisor::create_default_lpar() {
    // Create default LPAR for GameOS with standard privileges
    uint32_t gameos_lpar = create_lpar(0x10000000ULL, 0x00000001); // 256MB, basic privileges
    
    if (gameos_lpar != 0) {
        logger->info("Created default GameOS LPAR: %u", gameos_lpar);
    } else {
        logger->error("Failed to create default GameOS LPAR");
    }
}

bool Hypervisor::handle_memory_map(uint64_t* args, uint64_t* result) {
    uint32_t lpar_id = static_cast<uint32_t>(args[0]);
    uint64_t vaddr = args[1];
    uint64_t paddr = args[2];
    uint64_t size = args[3];
    uint32_t flags = static_cast<uint32_t>(args[4]);
    
    auto it = lpars.find(lpar_id);
    if (it == lpars.end()) {
        logger->error("Invalid LPAR ID for memory map: %u", lpar_id);
        *result = -1;
        return false;
    }
    
    bool success = memory_manager->map_memory(lpar_id, vaddr, paddr, size, flags);
    *result = success ? 0 : -1;
    
    if (success) {
        logger->debug("Mapped memory: LPAR=%u, vaddr=0x%016llX, paddr=0x%016llX, size=0x%016llX", 
                     lpar_id, vaddr, paddr, size);
    }
    
    return success;
}

bool Hypervisor::handle_memory_unmap(uint64_t* args, uint64_t* result) {
    uint32_t lpar_id = static_cast<uint32_t>(args[0]);
    uint64_t vaddr = args[1];
    uint64_t size = args[2];
    
    auto it = lpars.find(lpar_id);
    if (it == lpars.end()) {
        logger->error("Invalid LPAR ID for memory unmap: %u", lpar_id);
        *result = -1;
        return false;
    }
    
    bool success = memory_manager->unmap_memory(lpar_id, vaddr, size);
    *result = success ? 0 : -1;
    
    if (success) {
        logger->debug("Unmapped memory: LPAR=%u, vaddr=0x%016llX, size=0x%016llX", 
                     lpar_id, vaddr, size);
    }
    
    return success;
}

} // namespace Core
} // namespace GSCX