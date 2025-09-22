#include "cell_ir.h"
#include "logger.h"
#include <vector>
#include <cstring>
#include <algorithm>

namespace gscx::cell {

/**
 * @brief Decode PowerPC/SPU instruction block to simplified IR
 * @param code Raw instruction bytes
 * @param size Size of instruction block in bytes
 * @return Vector of decoded IR instructions
 * 
 * Assembly Integration Notes:
 * - PowerPC instructions are 4-byte aligned big-endian
 * - SPU instructions are 4-byte aligned little-endian
 * - Branch targets must be calculated relative to current PC
 */
std::vector<InstrIR> decode_block(const uint8_t* code, size_t size) {
    if (!code || size == 0) {
        Logger::warn("Decoder: Invalid input parameters");
        return {};
    }
    
    std::vector<InstrIR> out;
    out.reserve(size / 4); // Optimize memory allocation
    
    // Validate instruction alignment (4-byte boundary)
    if (size % 4 != 0) {
        Logger::warn("Decoder: Unaligned instruction block size");
    }
    
    // Process instructions in 4-byte chunks
    for (size_t offset = 0; offset < size; offset += 4) {
        if (offset + 4 > size) break;
        
        // Read 32-bit instruction (big-endian for PowerPC)
        uint32_t instr = (code[offset] << 24) | 
                        (code[offset + 1] << 16) |
                        (code[offset + 2] << 8) |
                         code[offset + 3];
        
        // TODO: Implement full PowerPC/SPU instruction decoding
        // For now, generate basic IR for demonstration
        if (instr == 0x60000000) { // PowerPC NOP (ori r0,r0,0)
            out.push_back({OpKind::Nop, {}, {}, {}});
        } else if ((instr & 0xFC000000) == 0x4C000000) { // Branch/Return family
            out.push_back({OpKind::Return, {}, {}, {}});
        } else {
            // Generic instruction placeholder
            out.push_back({OpKind::Nop, {}, {}, {}});
        }
    }
    
    // Ensure block ends with return for control flow
    if (out.empty() || out.back().op != OpKind::Return) {
        out.push_back({OpKind::Return, {}, {}, {}});
    }
    
    Logger::info("Decoder: Block decoded - " + std::to_string(out.size()) + " instructions");
    return out;
}

} // namespace gscx::cell