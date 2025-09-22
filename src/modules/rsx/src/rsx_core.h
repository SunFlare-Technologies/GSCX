/**
 * GSCX - PlayStation 3 High-Level Emulator
 * RSX (Reality Synthesizer) Core Header
 * 
 * This header defines the PS3's RSX graphics processor interface,
 * based on NVIDIA's G70/G71 architecture with custom modifications.
 */

#ifndef GSCX_MODULES_RSX_CORE_H
#define GSCX_MODULES_RSX_CORE_H

#include <cstdint>
#include <memory>
#include <vector>
#include <thread>
#include <atomic>
#include <mutex>

namespace GSCX {
namespace Core {
    class Logger;
}

namespace Modules {
namespace RSX {

/**
 * RSX Texture Unit
 * 
 * Represents a texture bound to a texture unit
 */
struct RSXTexture {
    uint64_t address;        // VRAM address of texture data
    uint32_t width;          // Texture width
    uint32_t height;         // Texture height
    uint32_t depth;          // Texture depth (for 3D textures)
    uint32_t format;         // Texture format
    uint32_t mipmap_levels;  // Number of mipmap levels
    uint32_t pitch;          // Texture pitch/stride
    bool enabled;            // Whether this texture unit is enabled
    
    RSXTexture() : address(0), width(0), height(0), depth(1), format(0), 
                   mipmap_levels(1), pitch(0), enabled(false) {}
};

/**
 * RSX Vertex Attribute
 * 
 * Describes a vertex attribute for vertex processing
 */
struct RSXVertexAttribute {
    uint64_t address;        // Address of vertex data
    uint32_t size;           // Size of attribute (1-4 components)
    uint32_t type;           // Data type (float, int, etc.)
    uint32_t stride;         // Stride between vertices
    bool normalized;         // Whether to normalize integer data
    bool enabled;            // Whether this attribute is enabled
    
    RSXVertexAttribute() : address(0), size(0), type(0), stride(0), 
                          normalized(false), enabled(false) {}
};

/**
 * RSX Render Target
 * 
 * Represents a render target (color or depth buffer)
 */
struct RSXRenderTarget {
    uint64_t address;        // VRAM address of render target
    uint32_t width;          // Render target width
    uint32_t height;         // Render target height
    uint32_t format;         // Pixel format
    uint32_t pitch;          // Pitch/stride in bytes
    bool enabled;            // Whether this render target is enabled
    
    RSXRenderTarget() : address(0), width(0), height(0), format(0), 
                       pitch(0), enabled(false) {}
};

/**
 * RSX Shader Program
 * 
 * Represents a vertex or fragment shader program
 */
struct RSXShaderProgram {
    uint64_t address;        // Address of shader code
    uint32_t size;           // Size of shader code
    uint32_t type;           // Shader type (vertex/fragment)
    bool enabled;            // Whether this shader is enabled
    
    RSXShaderProgram() : address(0), size(0), type(0), enabled(false) {}
};

/**
 * RSX Core Implementation
 * 
 * Main RSX graphics processor emulation class.
 * Handles graphics commands, state management, and rendering.
 */
class RSXCore {
public:
    RSXCore();
    ~RSXCore();
    
    // Core management
    bool initialize(uint64_t vram_addr, uint64_t ioif_addr);
    void shutdown();
    void reset_graphics_state();
    
    // State queries
    bool is_running() const { return running; }
    uint64_t get_vram_base() const { return vram_base; }
    uint64_t get_ioif_base() const { return ioif_base; }
    
    // Command processing
    void execute_method(uint32_t method, uint32_t arg);
    void wait_for_idle();
    
    // Surface management
    void set_surface_format(uint32_t format);
    void set_surface_pitch(uint32_t pitch);
    void set_surface_color_offset(uint32_t offset);
    void set_surface_zeta_offset(uint32_t offset);
    void clear_surface(uint32_t mask);
    
    // Viewport and clipping
    void set_viewport_horizontal(uint32_t value);
    void set_viewport_vertical(uint32_t value);
    void set_clip_min(uint32_t value);
    void set_clip_max(uint32_t value);
    void set_depth_range_near(uint32_t value);
    void set_depth_range_far(uint32_t value);
    
    // Drawing commands
    void draw_arrays(uint32_t mode, uint32_t first, uint32_t count);
    void draw_elements(uint32_t mode, uint32_t count, uint32_t type, uint64_t indices_addr);
    
    // Resource management
    void set_texture(uint32_t unit, const RSXTexture& texture);
    void set_vertex_attribute(uint32_t index, const RSXVertexAttribute& attribute);
    void set_render_target(uint32_t index, const RSXRenderTarget& target);
    
    // VRAM access
    uint8_t* get_vram_ptr(uint32_t offset);
    const uint8_t* get_vram_ptr(uint32_t offset) const;
    void write_vram(uint32_t offset, const void* data, uint32_t size);
    void read_vram(uint32_t offset, void* data, uint32_t size) const;
    
    // Statistics
    uint64_t get_draw_calls() const { return draw_calls; }
    uint64_t get_triangles_rendered() const { return triangles_rendered; }
    void reset_statistics() { draw_calls = 0; triangles_rendered = 0; }
    
private:
    std::unique_ptr<Core::Logger> logger;
    
    // Core state
    std::atomic<bool> running;
    uint64_t vram_base;
    uint64_t ioif_base;
    
    // VRAM
    std::vector<uint8_t> vram;
    
    // Command processing
    std::atomic<bool> command_processor_running;
    std::thread command_processor_thread;
    std::vector<uint8_t> command_buffer;
    
    // Graphics state
    uint32_t current_context_dma_color;
    uint32_t current_context_dma_zeta;
    uint32_t current_surface_format;
    uint32_t current_surface_pitch;
    uint32_t current_color_offset;
    uint32_t current_zeta_offset;
    
    // Viewport state
    uint32_t viewport_x, viewport_y;
    uint32_t viewport_width, viewport_height;
    float clip_min_z, clip_max_z;
    float depth_range_near, depth_range_far;
    
    // Resource arrays
    std::vector<RSXTexture> texture_units;
    std::vector<RSXVertexAttribute> vertex_attributes;
    std::vector<RSXRenderTarget> render_targets;
    
    // Shader programs
    RSXShaderProgram vertex_program;
    RSXShaderProgram fragment_program;
    
    // Statistics
    std::atomic<uint64_t> draw_calls;
    std::atomic<uint64_t> triangles_rendered;
    
    // Synchronization
    std::mutex state_mutex;
    
    // Internal methods
    void start_command_processor();
    void stop_command_processor();
    void command_processor_loop();
    void process_command_buffer();
};

/**
 * RSX Manager
 * 
 * System-wide RSX management for the PS3 emulator.
 * Handles RSX initialization, memory management, and display output.
 */
class RSXManager {
public:
    RSXManager();
    ~RSXManager();
    
    // Initialization
    bool initialize();
    void shutdown();
    
    // Core access
    RSXCore* get_core() { return rsx_core.get(); }
    const RSXCore* get_core() const { return rsx_core.get(); }
    
    // Display management
    bool create_display_buffer(uint32_t width, uint32_t height, uint32_t format);
    void present_display_buffer();
    void swap_buffers();
    
    // Memory management
    uint64_t allocate_vram(uint32_t size, uint32_t alignment = 256);
    void free_vram(uint64_t address);
    bool map_system_memory(uint64_t system_addr, uint64_t rsx_addr, uint32_t size);
    void unmap_system_memory(uint64_t rsx_addr, uint32_t size);
    
    // Status queries
    bool is_initialized() const { return initialized; }
    uint32_t get_vram_usage() const;
    uint32_t get_vram_free() const;
    
private:
    std::unique_ptr<Core::Logger> logger;
    std::unique_ptr<RSXCore> rsx_core;
    
    bool initialized;
    
    // Display state
    uint32_t display_width;
    uint32_t display_height;
    uint32_t display_format;
    
    // Memory management
    struct VRAMBlock {
        uint64_t address;
        uint32_t size;
        bool allocated;
    };
    
    std::vector<VRAMBlock> vram_blocks;
    std::mutex vram_mutex;
    
    // System memory mapping
    struct MemoryMapping {
        uint64_t system_addr;
        uint64_t rsx_addr;
        uint32_t size;
    };
    
    std::vector<MemoryMapping> memory_mappings;
    std::mutex mapping_mutex;
};

// RSX Surface Formats
enum RSXSurfaceFormat {
    RSX_SURFACE_FORMAT_B8 = 0x01,
    RSX_SURFACE_FORMAT_G8B8 = 0x02,
    RSX_SURFACE_FORMAT_A8R8G8B8 = 0x05,
    RSX_SURFACE_FORMAT_B8G8R8A8 = 0x06,
    RSX_SURFACE_FORMAT_R5G6B5 = 0x07,
    RSX_SURFACE_FORMAT_X8R8G8B8 = 0x08,
    RSX_SURFACE_FORMAT_B8G8R8X8 = 0x09,
    RSX_SURFACE_FORMAT_X1R5G5B5 = 0x0A,
    RSX_SURFACE_FORMAT_A1R5G5B5 = 0x0B,
    RSX_SURFACE_FORMAT_A4R4G4B4 = 0x0C,
    RSX_SURFACE_FORMAT_R32_FLOAT = 0x0D,
    RSX_SURFACE_FORMAT_R16_FLOAT = 0x0E,
    RSX_SURFACE_FORMAT_X8B8G8R8 = 0x0F,
    RSX_SURFACE_FORMAT_A8B8G8R8 = 0x10,
    RSX_SURFACE_FORMAT_B8G8R8 = 0x11,
    RSX_SURFACE_FORMAT_G8R8 = 0x12,
    RSX_SURFACE_FORMAT_R8 = 0x13
};

// RSX Depth Formats
enum RSXDepthFormat {
    RSX_DEPTH_FORMAT_Z16 = 0x01,
    RSX_DEPTH_FORMAT_Z24S8 = 0x02
};

// RSX Texture Formats
enum RSXTextureFormat {
    RSX_TEXTURE_FORMAT_B8 = 0x81,
    RSX_TEXTURE_FORMAT_A1R5G5B5 = 0x82,
    RSX_TEXTURE_FORMAT_A4R4G4B4 = 0x83,
    RSX_TEXTURE_FORMAT_R5G6B5 = 0x84,
    RSX_TEXTURE_FORMAT_A8R8G8B8 = 0x85,
    RSX_TEXTURE_FORMAT_DXT1 = 0x86,
    RSX_TEXTURE_FORMAT_DXT3 = 0x87,
    RSX_TEXTURE_FORMAT_DXT5 = 0x88,
    RSX_TEXTURE_FORMAT_G8B8 = 0x8B,
    RSX_TEXTURE_FORMAT_R6G5B5 = 0x8F,
    RSX_TEXTURE_FORMAT_DEPTH24_D8 = 0x90,
    RSX_TEXTURE_FORMAT_DEPTH24_D8_FLOAT = 0x91,
    RSX_TEXTURE_FORMAT_DEPTH16 = 0x92,
    RSX_TEXTURE_FORMAT_DEPTH16_FLOAT = 0x93,
    RSX_TEXTURE_FORMAT_X16 = 0x94,
    RSX_TEXTURE_FORMAT_Y16_X16 = 0x95,
    RSX_TEXTURE_FORMAT_R5G5B5A1 = 0x97,
    RSX_TEXTURE_FORMAT_W16_Z16_Y16_X16_FLOAT = 0x9A,
    RSX_TEXTURE_FORMAT_W32_Z32_Y32_X32_FLOAT = 0x9B,
    RSX_TEXTURE_FORMAT_X32_FLOAT = 0x9C,
    RSX_TEXTURE_FORMAT_D1R5G5B5 = 0x9D,
    RSX_TEXTURE_FORMAT_D8R8G8B8 = 0x9E,
    RSX_TEXTURE_FORMAT_Y16_X16_FLOAT = 0x9F
};

// RSX Primitive Types
enum RSXPrimitiveType {
    RSX_PRIMITIVE_POINTS = 0x01,
    RSX_PRIMITIVE_LINES = 0x02,
    RSX_PRIMITIVE_LINE_LOOP = 0x03,
    RSX_PRIMITIVE_LINE_STRIP = 0x04,
    RSX_PRIMITIVE_TRIANGLES = 0x05,
    RSX_PRIMITIVE_TRIANGLE_STRIP = 0x06,
    RSX_PRIMITIVE_TRIANGLE_FAN = 0x07,
    RSX_PRIMITIVE_QUADS = 0x08,
    RSX_PRIMITIVE_QUAD_STRIP = 0x09,
    RSX_PRIMITIVE_POLYGON = 0x0A
};

// RSX Vertex Attribute Types
enum RSXVertexAttributeType {
    RSX_VERTEX_ATTR_TYPE_FLOAT = 0x02,
    RSX_VERTEX_ATTR_TYPE_HALF_FLOAT = 0x03,
    RSX_VERTEX_ATTR_TYPE_UNSIGNED_BYTE = 0x04,
    RSX_VERTEX_ATTR_TYPE_SHORT = 0x05,
    RSX_VERTEX_ATTR_TYPE_COMPRESSED_NORMAL = 0x06
};

// RSX Clear Masks
enum RSXClearMask {
    RSX_CLEAR_COLOR = 0x01,
    RSX_CLEAR_DEPTH = 0x02,
    RSX_CLEAR_STENCIL = 0x04
};

} // namespace RSX
} // namespace Modules
} // namespace GSCX

#endif // GSCX_MODULES_RSX_CORE_H