/**
 * GSCX - PlayStation 3 High-Level Emulator
 * PPU (PowerPC Processing Unit) Core Header
 * 
 * This header defines the main PowerPC processor core interface
 * for the Cell Broadband Engine's PPU implementation.
 */

#ifndef GSCX_MODULES_CELL_PPU_CORE_H
#define GSCX_MODULES_CELL_PPU_CORE_H

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
 * PPU Vector Register (AltiVec/VMX)
 * 
 * 128-bit vector register for SIMD operations
 */
union PPUVectorRegister {
    uint8_t  u8[16];     // 16 unsigned bytes
    int8_t   s8[16];     // 16 signed bytes
    uint16_t u16[8];     // 8 unsigned halfwords
    int16_t  s16[8];     // 8 signed halfwords
    uint32_t u32[4];     // 4 unsigned words
    int32_t  s32[4];     // 4 signed words
    uint64_t u64[2];     // 2 unsigned doublewords
    int64_t  s64[2];     // 2 signed doublewords
    float    f32[4];     // 4 single-precision floats
    double   f64[2];     // 2 double-precision floats
};

/**
 * PPU Core Implementation
 * 
 * Implements the main PowerPC processor core with:
 * - 64-bit PowerPC architecture
 * - 32 General Purpose Registers (GPRs)
 * - 32 Floating Point Registers (FPRs)
 * - 32 Vector Registers (VRs) for AltiVec
 * - Complete instruction set support
 */
class PPUCore {
public:
    PPUCore();
    ~PPUCore();
    
    // Core management
    bool load_program(const uint8_t* program_data, uint32_t size, uint64_t entry_point);
    void start();
    void stop();
    void halt();
    
    // State queries
    bool is_running() const { return running; }
    bool is_halted() const { return halted; }
    uint64_t get_pc() const { return pc; }
    
    // Register access
    uint64_t get_gpr(uint32_t reg_num) const { return gpr[reg_num & 0x1F]; }
    void set_gpr(uint32_t reg_num, uint64_t value) { gpr[reg_num & 0x1F] = value; }
    
    double get_fpr(uint32_t reg_num) const { return fpr[reg_num & 0x1F]; }
    void set_fpr(uint32_t reg_num, double value) { fpr[reg_num & 0x1F] = value; }
    
    const PPUVectorRegister& get_vr(uint32_t reg_num) const { return vr[reg_num & 0x1F]; }
    void set_vr(uint32_t reg_num, const PPUVectorRegister& value) { vr[reg_num & 0x1F] = value; }
    
    // Special register access
    uint64_t get_lr() const { return lr; }
    void set_lr(uint64_t value) { lr = value; }
    
    uint64_t get_ctr() const { return ctr; }
    void set_ctr(uint64_t value) { ctr = value; }
    
    uint32_t get_cr() const { return cr; }
    void set_cr(uint32_t value) { cr = value; }
    
    uint32_t get_xer() const { return xer; }
    void set_xer(uint32_t value) { xer = value; }
    
    uint64_t get_msr() const { return msr; }
    void set_msr(uint64_t value) { msr = value; }
    
private:
    std::unique_ptr<Core::Logger> logger;
    
    // Execution state
    std::atomic<bool> running;
    std::atomic<bool> halted;
    
    // Program counter
    uint64_t pc;
    
    // General Purpose Registers (64-bit)
    uint64_t gpr[32];
    
    // Floating Point Registers (double precision)
    double fpr[32];
    
    // Vector Registers (AltiVec/VMX)
    PPUVectorRegister vr[32];
    
    // Special Purpose Registers
    uint64_t lr;   // Link Register
    uint64_t ctr;  // Count Register
    uint32_t cr;   // Condition Register
    uint32_t xer;  // Fixed-Point Exception Register
    uint64_t msr;  // Machine State Register
    uint32_t fpscr; // Floating-Point Status and Control Register
    uint32_t vscr;  // Vector Status and Control Register
    
    // Execution thread
    std::thread execution_thread;
    
    // Core execution functions
    void execute_loop();
    uint32_t fetch_instruction();
    void execute_instruction(uint32_t instruction);
    void handle_interrupts();
    
    // Integer arithmetic instructions
    void execute_addi(uint32_t rt, uint32_t ra, uint16_t immediate);
    void execute_addis(uint32_t rt, uint32_t ra, uint16_t immediate);
    void execute_extended_31(uint32_t instruction, uint32_t xo, uint32_t rt, uint32_t ra, uint32_t rb);
    
    // Load/Store instructions
    void execute_lwz(uint32_t rt, uint32_t ra, uint16_t displacement);
    void execute_stw(uint32_t rs, uint32_t ra, uint16_t displacement);
    void execute_lbz(uint32_t rt, uint32_t ra, uint16_t displacement);
    void execute_stb(uint32_t rs, uint32_t ra, uint16_t displacement);
    
    // Branch instructions
    void execute_bc(uint32_t instruction);
    void execute_b(uint32_t instruction);
    
    // Logical instructions
    void execute_ori(uint32_t rt, uint32_t ra, uint16_t immediate);
    void execute_oris(uint32_t rt, uint32_t ra, uint16_t immediate);
    void execute_andi(uint32_t rt, uint32_t ra, uint16_t immediate);
    void execute_andis(uint32_t rt, uint32_t ra, uint16_t immediate);
    
    // System instructions
    void execute_sc();
    
    // Helper functions
    void handle_syscall(uint64_t syscall_num);
    void update_cr0(uint64_t value);
};

/**
 * PPU Thread
 * 
 * Represents a single PPU thread with its own execution context.
 * PS3 applications can create multiple PPU threads.
 */
class PPUThread {
public:
    explicit PPUThread(uint32_t thread_id);
    ~PPUThread();
    
    // Thread management
    bool create(uint64_t entry_point, uint64_t stack_addr, uint64_t stack_size);
    void start();
    void stop();
    void join();
    
    // State queries
    uint32_t get_thread_id() const { return thread_id; }
    bool is_running() const;
    
    // Context access
    PPUCore* get_core() { return core.get(); }
    const PPUCore* get_core() const { return core.get(); }
    
private:
    std::unique_ptr<Core::Logger> logger;
    uint32_t thread_id;
    std::unique_ptr<PPUCore> core;
    
    // Thread context
    uint64_t entry_point;
    uint64_t stack_addr;
    uint64_t stack_size;
};

/**
 * PPU Manager
 * 
 * System-wide PPU management for the PS3 emulator.
 * Handles thread creation, scheduling, and resource management.
 */
class PPUManager {
public:
    PPUManager();
    ~PPUManager();
    
    // Initialization
    bool initialize();
    void shutdown();
    
    // Thread management
    uint32_t create_thread(uint64_t entry_point, uint64_t stack_addr, uint64_t stack_size);
    bool destroy_thread(uint32_t thread_id);
    PPUThread* get_thread(uint32_t thread_id);
    
    // Main thread access
    PPUThread* get_main_thread() { return main_thread.get(); }
    
    // Status queries
    uint32_t get_thread_count() const;
    std::vector<uint32_t> get_active_threads() const;
    
private:
    std::unique_ptr<Core::Logger> logger;
    
    // Main PPU thread (always exists)
    std::unique_ptr<PPUThread> main_thread;
    
    // Additional PPU threads
    std::map<uint32_t, std::unique_ptr<PPUThread>> threads;
    uint32_t next_thread_id;
    
    // Synchronization
    std::mutex thread_mutex;
};

// PowerPC instruction opcodes (primary opcodes)
enum PPUOpcodes {
    PPU_TWI = 0x03,      // Trap Word Immediate
    PPU_MULLI = 0x07,    // Multiply Low Immediate
    PPU_SUBFIC = 0x08,   // Subtract From Immediate Carrying
    PPU_CMPLI = 0x0A,    // Compare Logical Immediate
    PPU_CMPI = 0x0B,     // Compare Immediate
    PPU_ADDIC = 0x0C,    // Add Immediate Carrying
    PPU_ADDIC_DOT = 0x0D, // Add Immediate Carrying and Record
    PPU_ADDI = 0x0E,     // Add Immediate
    PPU_ADDIS = 0x0F,    // Add Immediate Shifted
    PPU_BC = 0x10,       // Branch Conditional
    PPU_SC = 0x11,       // System Call
    PPU_B = 0x12,        // Branch
    PPU_MCRF = 0x13,     // Move Condition Register Field
    PPU_ORI = 0x18,      // OR Immediate
    PPU_ORIS = 0x19,     // OR Immediate Shifted
    PPU_XORI = 0x1A,     // XOR Immediate
    PPU_XORIS = 0x1B,    // XOR Immediate Shifted
    PPU_ANDI_DOT = 0x1C, // AND Immediate
    PPU_ANDIS_DOT = 0x1D, // AND Immediate Shifted
    PPU_EXTENDED_31 = 0x1F, // Extended opcodes
    PPU_LWZ = 0x20,      // Load Word and Zero
    PPU_LWZU = 0x21,     // Load Word and Zero with Update
    PPU_LBZ = 0x22,      // Load Byte and Zero
    PPU_LBZU = 0x23,     // Load Byte and Zero with Update
    PPU_STW = 0x24,      // Store Word
    PPU_STWU = 0x25,     // Store Word with Update
    PPU_STB = 0x26,      // Store Byte
    PPU_STBU = 0x27,     // Store Byte with Update
    PPU_LHZ = 0x28,      // Load Halfword and Zero
    PPU_LHZU = 0x29,     // Load Halfword and Zero with Update
    PPU_LHA = 0x2A,      // Load Halfword Algebraic
    PPU_LHAU = 0x2B,     // Load Halfword Algebraic with Update
    PPU_STH = 0x2C,      // Store Halfword
    PPU_STHU = 0x2D,     // Store Halfword with Update
    PPU_LMW = 0x2E,      // Load Multiple Word
    PPU_STMW = 0x2F      // Store Multiple Word
};

// Extended opcode 31 instructions
enum PPUExtended31Opcodes {
    PPU_CMP = 0x000,     // Compare
    PPU_TW = 0x004,      // Trap Word
    PPU_SUBFC = 0x008,   // Subtract From Carrying
    PPU_MULHDU = 0x009,  // Multiply High Doubleword Unsigned
    PPU_ADDC = 0x00A,    // Add Carrying
    PPU_MULHWU = 0x00B,  // Multiply High Word Unsigned
    PPU_MFCR = 0x013,    // Move From Condition Register
    PPU_LWARX = 0x014,   // Load Word And Reserve Indexed
    PPU_LDXL = 0x015,    // Load Doubleword Indexed
    PPU_LWZX = 0x017,    // Load Word and Zero Indexed
    PPU_SLW = 0x018,     // Shift Left Word
    PPU_CNTLZW = 0x01A,  // Count Leading Zeros Word
    PPU_SLD = 0x01B,     // Shift Left Doubleword
    PPU_AND = 0x01C,     // AND
    PPU_CMPL = 0x020,    // Compare Logical
    PPU_SUBF = 0x028,    // Subtract From
    PPU_LDUX = 0x035,    // Load Doubleword with Update Indexed
    PPU_DCBST = 0x036,   // Data Cache Block Store
    PPU_LWZUX = 0x037,   // Load Word and Zero with Update Indexed
    PPU_CNTLZD = 0x03A,  // Count Leading Zeros Doubleword
    PPU_ANDC = 0x03C,    // AND with Complement
    PPU_MULHD = 0x049,   // Multiply High Doubleword
    PPU_MULHW = 0x04B,   // Multiply High Word
    PPU_NEG = 0x068,     // Negate
    PPU_MULT = 0x0EB,    // Multiply Low
    PPU_MULLD = 0x0E9,   // Multiply Low Doubleword
    PPU_ADD = 0x10A,     // Add
    PPU_DCBF = 0x056,    // Data Cache Block Flush
    PPU_LBZX = 0x057,    // Load Byte and Zero Indexed
    PPU_LVX = 0x067,     // Load Vector Indexed
    PPU_NOR = 0x07C,     // NOR
    PPU_SUBFE = 0x088,   // Subtract From Extended
    PPU_ADDE = 0x08A,    // Add Extended
    PPU_MTCRF = 0x090,   // Move To Condition Register Fields
    PPU_STDX = 0x095,    // Store Doubleword Indexed
    PPU_STWCX_DOT = 0x096, // Store Word Conditional Indexed
    PPU_STWX = 0x097,    // Store Word Indexed
    PPU_STDUX = 0x0B5,   // Store Doubleword with Update Indexed
    PPU_STWUX = 0x0B7,   // Store Word with Update Indexed
    PPU_SUBFZE = 0x0C8,  // Subtract From Zero Extended
    PPU_ADDZE = 0x0CA,   // Add to Zero Extended
    PPU_STDCX_DOT = 0x0D6, // Store Doubleword Conditional Indexed
    PPU_STBX = 0x0D7,    // Store Byte Indexed
    PPU_SUBFME = 0x0E8,  // Subtract From Minus One Extended
    PPU_MULLD = 0x0E9,   // Multiply Low Doubleword
    PPU_ADDME = 0x0EA,   // Add to Minus One Extended
    PPU_MULLW = 0x0EB,   // Multiply Low Word
    PPU_DCBTST = 0x0F6,  // Data Cache Block Touch for Store
    PPU_STBUX = 0x0F7,   // Store Byte with Update Indexed
    PPU_DOZ = 0x108,     // Difference or Zero
    PPU_ADD = 0x10A,     // Add
    PPU_DCBT = 0x116,    // Data Cache Block Touch
    PPU_LHZX = 0x117,    // Load Halfword and Zero Indexed
    PPU_EQV = 0x11C,     // Equivalent
    PPU_ECIWX = 0x136,   // External Control In Word Indexed
    PPU_LHZUX = 0x137,   // Load Halfword and Zero with Update Indexed
    PPU_XOR = 0x13C,     // XOR
    PPU_MFSPR = 0x153,   // Move From Special Purpose Register
    PPU_LWAX = 0x155,    // Load Word Algebraic Indexed
    PPU_LHAX = 0x157,    // Load Halfword Algebraic Indexed
    PPU_LVXL = 0x167,    // Load Vector Indexed LRU
    PPU_MFTB = 0x173,    // Move From Time Base
    PPU_LWAUX = 0x175,   // Load Word Algebraic with Update Indexed
    PPU_LHAUX = 0x177,   // Load Halfword Algebraic with Update Indexed
    PPU_STHX = 0x197,    // Store Halfword Indexed
    PPU_ORC = 0x19C,     // OR with Complement
    PPU_ECOWX = 0x1B6,   // External Control Out Word Indexed
    PPU_STHUX = 0x1B7,   // Store Halfword with Update Indexed
    PPU_OR = 0x1BC,      // OR
    PPU_DIVDU = 0x1C9,   // Divide Doubleword Unsigned
    PPU_DIVWU = 0x1CB,   // Divide Word Unsigned
    PPU_MTSPR = 0x1D3,   // Move To Special Purpose Register
    PPU_DCBI = 0x1D6,    // Data Cache Block Invalidate
    PPU_NAND = 0x1DC,    // NAND
    PPU_STVXL = 0x1E7,   // Store Vector Indexed LRU
    PPU_DIVD = 0x1E9,    // Divide Doubleword
    PPU_DIVW = 0x1EB,    // Divide Word
    PPU_LVSL = 0x00C,    // Load Vector for Shift Left
    PPU_LVSR = 0x04C,    // Load Vector for Shift Right
    PPU_MFVSCR = 0x604,  // Move From Vector Status and Control Register
    PPU_MTVSCR = 0x644,  // Move To Vector Status and Control Register
    PPU_VADDCUW = 0x180, // Vector Add Carryout Unsigned Word
    PPU_VADDFP = 0x00A,  // Vector Add Single-Precision
    PPU_VADDSBS = 0x300, // Vector Add Signed Byte Saturate
    PPU_VADDSHS = 0x340, // Vector Add Signed Halfword Saturate
    PPU_VADDSWS = 0x380, // Vector Add Signed Word Saturate
    PPU_VADDUBM = 0x000, // Vector Add Unsigned Byte Modulo
    PPU_VADDUBS = 0x200, // Vector Add Unsigned Byte Saturate
    PPU_VADDUHM = 0x040, // Vector Add Unsigned Halfword Modulo
    PPU_VADDUHS = 0x240, // Vector Add Unsigned Halfword Saturate
    PPU_VADDUWM = 0x080, // Vector Add Unsigned Word Modulo
    PPU_VADDUWS = 0x280  // Vector Add Unsigned Word Saturate
};

} // namespace CellCPU
} // namespace Modules
} // namespace GSCX

#endif // GSCX_MODULES_CELL_PPU_CORE_H