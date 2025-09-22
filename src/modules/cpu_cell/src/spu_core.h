/**
 * GSCX - PlayStation 3 High-Level Emulator
 * SPU (Synergistic Processing Unit) Core Header
 * 
 * This header defines the SPU processor core interface and structures
 * for the Cell Broadband Engine's SPU implementation.
 */

#ifndef GSCX_MODULES_CELL_SPU_CORE_H
#define GSCX_MODULES_CELL_SPU_CORE_H

#include <cstdint>
#include <memory>
#include <thread>
#include <atomic>

namespace GSCX {
namespace Core {
    class Logger;
}

namespace Modules {
namespace CellCPU {

/**
 * SPU Register Structure
 * 
 * SPU registers are 128-bit (16 bytes) and can be accessed
 * as different data types for SIMD operations.
 */
union SPURegister {
    uint8_t  byte[16];      // 16 bytes
    uint16_t halfword[8];   // 8 halfwords
    uint32_t word[4];       // 4 words
    uint64_t dword[2];      // 2 doublewords
    float    single[4];     // 4 single-precision floats
    double   double_val[2]; // 2 double-precision floats
    
    // Vector types for SIMD operations
    struct {
        uint32_t x, y, z, w;
    } vec4u;
    
    struct {
        float x, y, z, w;
    } vec4f;
};

/**
 * SPU Core Implementation
 * 
 * Implements a single SPU processor core with:
 * - 256KB Local Store (LS)
 * - 128 x 128-bit registers
 * - SIMD instruction execution
 * - DMA operations
 */
class SPUCore {
public:
    explicit SPUCore(uint32_t spu_id);
    ~SPUCore();
    
    // Core management
    bool load_program(const uint8_t* program_data, uint32_t size, uint32_t entry_point);
    void start();
    void stop();
    void halt();
    
    // State queries
    bool is_running() const { return running; }
    bool is_halted() const { return halted; }
    uint32_t get_pc() const { return pc; }
    uint32_t get_spu_id() const { return spu_id; }
    
    // Register access
    const SPURegister& get_register(uint32_t reg_num) const {
        return registers[reg_num & 0x7F];  // Mask to 0-127
    }
    
    void set_register(uint32_t reg_num, const SPURegister& value) {
        registers[reg_num & 0x7F] = value;
    }
    
    // Local store access
    uint8_t* get_local_store() { return local_store.get(); }
    const uint8_t* get_local_store() const { return local_store.get(); }
    
    // DMA operations
    bool dma_get(uint32_t ls_addr, uint64_t ea_addr, uint32_t size, uint32_t tag);
    bool dma_put(uint32_t ls_addr, uint64_t ea_addr, uint32_t size, uint32_t tag);
    void dma_wait(uint32_t tag_mask);
    
private:
    std::unique_ptr<Core::Logger> logger;
    
    // SPU identification
    uint32_t spu_id;
    
    // Execution state
    std::atomic<bool> running;
    std::atomic<bool> halted;
    uint32_t pc;  // Program counter
    
    // SPU resources
    std::unique_ptr<uint8_t[]> local_store;     // 256KB Local Store
    std::unique_ptr<SPURegister[]> registers;   // 128 registers
    
    // Execution thread
    std::thread execution_thread;
    
    // Core execution functions
    void execute_loop();
    uint32_t fetch_instruction();
    void execute_instruction(uint32_t instruction);
    void handle_events();
    
    // Arithmetic instructions
    void execute_il(uint32_t rt, uint16_t immediate);
    void execute_ilh(uint32_t rt, uint16_t immediate);
    void execute_ilhu(uint32_t rt, uint16_t immediate);
    void execute_a(uint32_t rt, uint32_t ra, uint32_t rb);
    void execute_ah(uint32_t rt, uint32_t ra, uint32_t rb);
    void execute_sf(uint32_t rt, uint32_t ra, uint32_t rb);
    
    // Logical instructions
    void execute_and(uint32_t rt, uint32_t ra, uint32_t rb);
    void execute_or(uint32_t rt, uint32_t ra, uint32_t rb);
    void execute_xor(uint32_t rt, uint32_t ra, uint32_t rb);
    
    // Memory instructions
    void execute_lqa(uint32_t rt, uint16_t address);
    void execute_lqx(uint32_t rt, uint32_t ra, uint32_t rb);
    void execute_stqa(uint32_t rt, uint16_t address);
    void execute_stqx(uint32_t rt, uint32_t ra, uint32_t rb);
    
    // Branch instructions
    void execute_br(uint16_t offset);
    void execute_bra(uint16_t address);
    void execute_brz(uint32_t rt, uint16_t offset);
    void execute_brnz(uint32_t rt, uint16_t offset);
    
    // Special register access
    void execute_mfspr(uint32_t rt, uint32_t spr);
    void execute_mtspr(uint32_t rt, uint32_t spr);
    
    // Control instructions
    void execute_stop(uint32_t instruction);
};

/**
 * SPU Thread Group
 * 
 * Manages multiple SPU cores as a thread group,
 * which is how PS3 applications typically use SPUs.
 */
class SPUThreadGroup {
public:
    explicit SPUThreadGroup(uint32_t group_id);
    ~SPUThreadGroup();
    
    // Thread group management
    bool create_thread(uint32_t spu_id, const uint8_t* program, uint32_t size, uint32_t entry_point);
    bool destroy_thread(uint32_t spu_id);
    void start_all();
    void stop_all();
    void wait_all();
    
    // Status queries
    uint32_t get_group_id() const { return group_id; }
    size_t get_thread_count() const { return spu_threads.size(); }
    
private:
    std::unique_ptr<Core::Logger> logger;
    uint32_t group_id;
    std::vector<std::unique_ptr<SPUCore>> spu_threads;
};

/**
 * SPU Manager
 * 
 * System-wide SPU management for the PS3 emulator.
 * Handles SPU allocation, thread groups, and resource management.
 */
class SPUManager {
public:
    SPUManager();
    ~SPUManager();
    
    // Initialization
    bool initialize(uint32_t num_spus = 6);  // PS3 has 6 usable SPUs
    void shutdown();
    
    // Thread group management
    uint32_t create_thread_group();
    bool destroy_thread_group(uint32_t group_id);
    SPUThreadGroup* get_thread_group(uint32_t group_id);
    
    // SPU allocation
    uint32_t allocate_spu();
    void deallocate_spu(uint32_t spu_id);
    
    // Status queries
    uint32_t get_available_spus() const;
    bool is_spu_available(uint32_t spu_id) const;
    
private:
    std::unique_ptr<Core::Logger> logger;
    
    // SPU resources
    std::vector<std::unique_ptr<SPUCore>> spu_cores;
    std::vector<bool> spu_allocated;
    
    // Thread groups
    std::map<uint32_t, std::unique_ptr<SPUThreadGroup>> thread_groups;
    uint32_t next_group_id;
    
    // Synchronization
    std::mutex spu_mutex;
    std::mutex group_mutex;
};

// SPU instruction opcodes (partial list)
enum SPUOpcodes {
    SPU_STOP = 0x000,
    SPU_LNOP = 0x001,
    SPU_IL = 0x040,
    SPU_ILH = 0x041,
    SPU_ILHU = 0x042,
    SPU_A = 0x080,
    SPU_AH = 0x081,
    SPU_SF = 0x088,
    SPU_AND = 0x0C0,
    SPU_OR = 0x0C1,
    SPU_XOR = 0x0C2,
    SPU_LQA = 0x100,
    SPU_LQX = 0x101,
    SPU_STQA = 0x104,
    SPU_STQX = 0x105,
    SPU_BR = 0x180,
    SPU_BRA = 0x181,
    SPU_BRZ = 0x182,
    SPU_BRNZ = 0x183,
    SPU_MFSPR = 0x200,
    SPU_MTSPR = 0x201
};

// SPU special registers
enum SPUSpecialRegisters {
    SPU_SPR_ID = 0,
    SPU_SPR_MACHINE_STATE = 1,
    SPU_SPR_NPC = 2,
    SPU_SPR_FPSCR = 3,
    SPU_SPR_SRESET = 4,
    SPU_SPR_LSLR = 5,
    SPU_SPR_DECR = 6,
    SPU_SPR_DECR_STATUS = 7
};

} // namespace CellCPU
} // namespace Modules
} // namespace GSCX

#endif // GSCX_MODULES_CELL_SPU_CORE_H