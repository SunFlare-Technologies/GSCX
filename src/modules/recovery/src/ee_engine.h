#pragma once
#include "recovery_i18n.h"
#include "host_services_c.h"
#include <cstdint>
#include <memory>
#include <vector>
#include <string>

namespace gscx {
namespace recovery {

// EE (Emotion Engine) CPU Registers
struct EERegisters {
    // General Purpose Registers (128-bit)
    uint64_t gpr[32][2];  // 32 registers, 128-bit each (stored as 2x64-bit)
    
    // Special Registers
    uint64_t pc;          // Program Counter
    uint64_t hi, lo;      // Multiply/Divide results
    uint64_t hi1, lo1;    // Additional hi/lo for parallel operations
    
    // Floating Point Registers
    float fpr[32];        // 32 floating point registers
    uint32_t fcr[32];     // Floating point control registers
    
    // Vector Unit Registers (VU0/VU1)
    float vf[32][4];      // Vector float registers (x,y,z,w)
    uint16_t vi[16];      // Vector integer registers
    
    // System Control Registers
    uint32_t status;      // Status register
    uint32_t cause;       // Cause register
    uint32_t epc;         // Exception PC
    uint32_t badvaddr;    // Bad virtual address
};

// EE Memory Management
struct EEMemoryMap {
    static constexpr uint32_t MAIN_RAM_SIZE = 32 * 1024 * 1024;  // 32MB
    static constexpr uint32_t SCRATCH_PAD_SIZE = 16 * 1024;      // 16KB
    static constexpr uint32_t BIOS_SIZE = 4 * 1024 * 1024;       // 4MB
    
    static constexpr uint32_t MAIN_RAM_BASE = 0x00000000;
    static constexpr uint32_t SCRATCH_PAD_BASE = 0x70000000;
    static constexpr uint32_t BIOS_BASE = 0x1FC00000;
    static constexpr uint32_t IOP_RAM_BASE = 0x1C000000;
};

// EE Instruction Types
enum class EEInstructionType {
    ARITHMETIC,
    LOGICAL,
    SHIFT,
    BRANCH,
    JUMP,
    LOAD_STORE,
    MULTIPLY_DIVIDE,
    VECTOR,
    SYSTEM,
    UNKNOWN
};

// EE Instruction Structure
struct EEInstruction {
    uint32_t raw;                    // Raw 32-bit instruction
    EEInstructionType type;
    uint8_t opcode;                  // Primary opcode
    uint8_t rs, rt, rd;             // Register fields
    uint16_t immediate;              // Immediate value
    uint32_t target;                 // Jump target
    uint8_t function;                // Function code
    uint8_t shamt;                   // Shift amount
};

// EE Exception Types
enum class EEException {
    NONE,
    INTERRUPT,
    TLB_MISS,
    ADDRESS_ERROR,
    BUS_ERROR,
    SYSCALL,
    BREAKPOINT,
    RESERVED_INSTRUCTION,
    COPROCESSOR_UNUSABLE,
    OVERFLOW,
    TRAP
};

// Forward declarations
class VectorUnit;
class IOProcessor;

// Main EE (Emotion Engine) Class
class EmotionEngine {
public:
    EmotionEngine(HostServicesC* host);
    ~EmotionEngine();

    // Core functions
    bool initialize();
    void shutdown();
    void reset();
    
    // Execution
    void execute_cycle();
    void execute_instruction(const EEInstruction& instr);
    
    // Memory operations
    uint32_t read_memory32(uint32_t address);
    uint16_t read_memory16(uint32_t address);
    uint8_t read_memory8(uint32_t address);
    
    void write_memory32(uint32_t address, uint32_t value);
    void write_memory16(uint32_t address, uint16_t value);
    void write_memory8(uint32_t address, uint8_t value);
    
    // Register access
    uint64_t get_gpr(int reg) const;
    void set_gpr(int reg, uint64_t value);
    
    uint64_t get_pc() const { return registers_.pc; }
    void set_pc(uint64_t pc) { registers_.pc = pc; }
    
    // Exception handling
    void trigger_exception(EEException exception);
    void handle_interrupt(uint32_t interrupt_mask);
    
    // Vector Units
    VectorUnit* get_vu0() { return vu0_.get(); }
    VectorUnit* get_vu1() { return vu1_.get(); }
    
    // IOP interface
    IOProcessor* get_iop() { return iop_.get(); }
    
    // Debugging
    void dump_registers() const;
    void dump_memory(uint32_t start, uint32_t size) const;
    
    // Performance counters
    uint64_t get_cycle_count() const { return cycle_count_; }
    uint64_t get_instruction_count() const { return instruction_count_; }
    
private:
    // Internal functions
    void log_info(const std::string& message);
    void log_warn(const std::string& message);
    void log_error(const std::string& message);
    
    EEInstruction decode_instruction(uint32_t raw);
    
    // Instruction execution
    void execute_arithmetic(const EEInstruction& instr);
    void execute_logical(const EEInstruction& instr);
    void execute_shift(const EEInstruction& instr);
    void execute_branch(const EEInstruction& instr);
    void execute_jump(const EEInstruction& instr);
    void execute_load_store(const EEInstruction& instr);
    void execute_multiply_divide(const EEInstruction& instr);
    void execute_vector(const EEInstruction& instr);
    void execute_system(const EEInstruction& instr);
    
    // Memory management
    bool is_valid_address(uint32_t address) const;
    uint8_t* get_memory_pointer(uint32_t address);
    
    // Member variables
    HostServicesC* host_;
    EERegisters registers_;
    
    // Memory
    std::vector<uint8_t> main_ram_;
    std::vector<uint8_t> scratch_pad_;
    std::vector<uint8_t> bios_;
    
    // Subsystems
    std::unique_ptr<VectorUnit> vu0_;
    std::unique_ptr<VectorUnit> vu1_;
    std::unique_ptr<IOProcessor> iop_;
    
    // State
    bool initialized_;
    bool running_;
    
    // Performance counters
    uint64_t cycle_count_;
    uint64_t instruction_count_;
    
    // Exception state
    EEException pending_exception_;
    uint32_t exception_data_;
};

// Vector Unit Class (VU0/VU1)
class VectorUnit {
public:
    VectorUnit(int unit_id, HostServicesC* host);
    ~VectorUnit();
    
    bool initialize();
    void shutdown();
    void reset();
    
    // Execution
    void execute_micro_program(uint32_t start_address);
    void execute_vector_instruction(uint32_t instruction);
    
    // Memory
    uint32_t read_micro_mem(uint32_t address);
    void write_micro_mem(uint32_t address, uint32_t value);
    
    // Registers
    float get_vf_register(int reg, int component) const;
    void set_vf_register(int reg, int component, float value);
    
    uint16_t get_vi_register(int reg) const;
    void set_vi_register(int reg, uint16_t value);
    
private:
    int unit_id_;
    HostServicesC* host_;
    
    // VU Memory
    std::vector<uint32_t> micro_memory_;
    std::vector<uint8_t> data_memory_;
    
    // VU Registers
    float vf_registers_[32][4];  // Vector float registers
    uint16_t vi_registers_[16];  // Vector integer registers
    
    // State
    bool initialized_;
    uint32_t pc_;
    
    void log_info(const std::string& message);
};

// I/O Processor Class (simplified)
class IOProcessor {
public:
    IOProcessor(HostServicesC* host);
    ~IOProcessor();
    
    bool initialize();
    void shutdown();
    void reset();
    
    // Communication with EE
    void send_command(uint32_t command, uint32_t data);
    uint32_t receive_response();
    
    // IOP services
    void handle_syscall(uint32_t syscall_id);
    
private:
    HostServicesC* host_;
    bool initialized_;
    
    // IOP Memory
    std::vector<uint8_t> iop_ram_;
    
    void log_info(const std::string& message);
};

} // namespace recovery
} // namespace gscx