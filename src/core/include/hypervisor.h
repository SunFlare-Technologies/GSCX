/**
 * GSCX - PlayStation 3 High-Level Emulator
 * Hypervisor Header
 * 
 * This header defines the PS3 Hypervisor interface and structures
 * for managing system virtualization and security.
 */

#ifndef GSCX_CORE_HYPERVISOR_H
#define GSCX_CORE_HYPERVISOR_H

#include <cstdint>
#include <memory>
#include <vector>

namespace GSCX {
namespace Core {

// Forward declarations
class Logger;
class HVMemoryManager;
class HVSecurityManager;

/**
 * PS3 Hypervisor Implementation
 * 
 * The Hypervisor manages:
 * - Logical Partitions (LPARs)
 * - Memory virtualization
 * - Security and privilege management
 * - System resource allocation
 */
class Hypervisor {
public:
    Hypervisor();
    ~Hypervisor();
    
    // Core hypervisor functions
    bool initialize();
    void shutdown();
    
    // LPAR management
    uint32_t create_lpar(uint64_t size, uint32_t privileges);
    bool destroy_lpar(uint32_t lpar_id);
    
    // Hypervisor call interface
    bool handle_hvcall(uint32_t opcode, uint64_t* args, uint64_t* result);
    
    // Status queries
    bool is_initialized() const { return hv_initialized; }
    uint32_t get_version() const { return 0x00030041; }
    
private:
    std::unique_ptr<Logger> logger;
    std::unique_ptr<HVMemoryManager> memory_manager;
    std::unique_ptr<HVSecurityManager> security_manager;
    
    bool hv_initialized = false;
    
    // Internal functions
    void create_default_lpar();
    bool handle_memory_map(uint64_t* args, uint64_t* result);
    bool handle_memory_unmap(uint64_t* args, uint64_t* result);
};

/**
 * Hypervisor Memory Manager
 * 
 * Manages memory allocation and mapping for LPARs
 */
class HVMemoryManager {
public:
    HVMemoryManager() = default;
    ~HVMemoryManager() = default;
    
    bool initialize(uint64_t base_addr, uint64_t size);
    void shutdown();
    
    // LPAR memory management
    uint64_t allocate_lpar_memory(uint64_t size);
    void free_lpar_memory(uint64_t addr, uint64_t size);
    
    // Memory mapping
    bool map_memory(uint32_t lpar_id, uint64_t vaddr, uint64_t paddr, uint64_t size, uint32_t flags);
    bool unmap_memory(uint32_t lpar_id, uint64_t vaddr, uint64_t size);
    
    // Memory protection
    bool protect_memory(uint64_t addr, uint64_t size, uint32_t protection);
    
private:
    struct MemoryRegion {
        uint64_t base_addr;
        uint64_t size;
        uint32_t lpar_id;
        uint32_t flags;
        bool allocated;
    };
    
    std::vector<MemoryRegion> memory_regions;
    uint64_t hv_base_addr = 0;
    uint64_t hv_size = 0;
    uint64_t next_alloc_addr = 0;
};

/**
 * Hypervisor Security Manager
 * 
 * Handles privilege checking and security policies
 */
class HVSecurityManager {
public:
    HVSecurityManager() = default;
    ~HVSecurityManager() = default;
    
    bool initialize();
    void shutdown();
    
    // Privilege management
    bool check_privileges(uint32_t lpar_id, uint64_t required_privileges);
    bool grant_privileges(uint32_t lpar_id, uint64_t privileges);
    bool revoke_privileges(uint32_t lpar_id, uint64_t privileges);
    
    // Security policies
    bool validate_memory_access(uint32_t lpar_id, uint64_t addr, uint64_t size, uint32_t access_type);
    bool validate_syscall(uint32_t lpar_id, uint32_t syscall_id);
    
private:
    struct LPARPrivileges {
        uint32_t lpar_id;
        uint64_t granted_privileges;
        uint64_t denied_privileges;
    };
    
    std::vector<LPARPrivileges> lpar_privileges;
};

// Hypervisor call opcodes
enum HVCallOpcodes {
    HV_GET_VERSION = 0x1000,
    HV_CREATE_LPAR = 0x1001,
    HV_DESTROY_LPAR = 0x1002,
    HV_MEMORY_MAP = 0x2000,
    HV_MEMORY_UNMAP = 0x2001,
    HV_MEMORY_PROTECT = 0x2002,
    HV_SECURITY_CHECK = 0x3000,
    HV_GRANT_PRIVILEGES = 0x3001,
    HV_REVOKE_PRIVILEGES = 0x3002
};

// Memory protection flags
enum MemoryProtection {
    HV_MEM_READ = 0x01,
    HV_MEM_WRITE = 0x02,
    HV_MEM_EXECUTE = 0x04,
    HV_MEM_CACHED = 0x08,
    HV_MEM_COHERENT = 0x10
};

// LPAR privilege flags
enum LPARPrivileges {
    HV_PRIV_BASIC = 0x00000001,        // Basic LPAR operations
    HV_PRIV_MEMORY = 0x00000002,       // Memory management
    HV_PRIV_IO = 0x00000004,           // I/O operations
    HV_PRIV_INTERRUPT = 0x00000008,    // Interrupt handling
    HV_PRIV_SYSCALL = 0x00000010,      // System calls
    HV_PRIV_DEBUG = 0x00000020,        // Debug operations
    HV_PRIV_ADMIN = 0x80000000         // Administrative privileges
};

} // namespace Core
} // namespace GSCX

#endif // GSCX_CORE_HYPERVISOR_H