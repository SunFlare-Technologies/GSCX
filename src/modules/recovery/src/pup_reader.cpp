#include "pup_reader.h"
#include "../../../core/include/logger.h"
#include <iostream>
#include <filesystem>
#include <map>

namespace Recovery {

PUPReader::PUPReader() {
    pup_info_.is_valid = false;
    initialize_entry_descriptions();
}

PUPReader::~PUPReader() {
    if (file_stream_.is_open()) {
        file_stream_.close();
    }
}

void PUPReader::initialize_entry_descriptions() {
    // Known PUP entry IDs and their descriptions
    entry_descriptions_[0x100] = "System Software Update";
    entry_descriptions_[0x101] = "Recovery Mode";
    entry_descriptions_[0x102] = "System Software";
    entry_descriptions_[0x103] = "VTRM";
    entry_descriptions_[0x104] = "System Software (Backup)";
    entry_descriptions_[0x200] = "Kernel";
    entry_descriptions_[0x201] = "System Manager";
    entry_descriptions_[0x202] = "System Storage Manager";
    entry_descriptions_[0x300] = "Bootloader";
    entry_descriptions_[0x301] = "Updater";
    entry_descriptions_[0x302] = "System Files";
}

bool PUPReader::read_pup_file(const std::string& file_path) {
    Logger::log_info("[PUPReader] Reading PUP file: " + file_path);
    
    // Reset previous state
    pup_info_ = PUPFileInfo();
    pup_info_.file_path = file_path;
    
    if (file_stream_.is_open()) {
        file_stream_.close();
    }
    
    // Open file
    file_stream_.open(file_path, std::ios::binary);
    if (!file_stream_) {
        Logger::log_error("[PUPReader] Failed to open file: " + file_path);
        return false;
    }
    
    // Read and validate header
    if (!read_header()) {
        Logger::log_error("[PUPReader] Invalid PUP header");
        return false;
    }
    
    // Read entries table
    if (!read_entries()) {
        Logger::log_error("[PUPReader] Failed to read PUP entries");
        return false;
    }
    
    pup_info_.is_valid = true;
    Logger::log_info("[PUPReader] Successfully parsed PUP file with " + 
                    std::to_string(pup_info_.file_count) + " entries");
    
    return true;
}

bool PUPReader::read_header() {
    // Read magic header (8 bytes)
    char magic[8];
    file_stream_.read(magic, 8);
    if (!file_stream_ || !validate_magic(magic)) {
        return false;
    }
    
    // Read version (8 bytes)
    file_stream_.read(reinterpret_cast<char*>(&pup_info_.version), 8);
    if (!file_stream_) {
        return false;
    }
    
    // Read file count (8 bytes)
    file_stream_.read(reinterpret_cast<char*>(&pup_info_.file_count), 8);
    if (!file_stream_) {
        return false;
    }
    
    Logger::log_info("[PUPReader] PUP Version: 0x" + 
                    std::to_string(pup_info_.version) + 
                    ", File Count: " + std::to_string(pup_info_.file_count));
    
    return true;
}

bool PUPReader::read_entries() {
    pup_info_.entries.clear();
    pup_info_.entries.reserve(pup_info_.file_count);
    
    for (size_t i = 0; i < pup_info_.file_count; i++) {
        PUPEntry entry;
        uint32_t padding;
        
        // Read entry data (24 bytes total)
        file_stream_.read(reinterpret_cast<char*>(&entry.id), 4);
        file_stream_.read(reinterpret_cast<char*>(&padding), 4); // Skip padding
        file_stream_.read(reinterpret_cast<char*>(&entry.offset), 8);
        file_stream_.read(reinterpret_cast<char*>(&entry.size), 8);
        
        if (!file_stream_) {
            Logger::log_error("[PUPReader] Failed to read entry " + std::to_string(i));
            return false;
        }
        
        // Set description if known
        entry.description = get_entry_description(entry.id);
        
        pup_info_.entries.push_back(entry);
        
        Logger::log_info("[PUPReader] Entry " + std::to_string(i) + 
                        ": ID=0x" + std::to_string(entry.id) + 
                        ", Offset=" + std::to_string(entry.offset) + 
                        ", Size=" + std::to_string(entry.size) + 
                        ", Desc=" + entry.description);
    }
    
    return true;
}

bool PUPReader::validate_magic(const char* magic) const {
    // Check for "SCEUF" magic (first 5 bytes)
    return std::string(magic, 5) == "SCEUF";
}

const PUPEntry* PUPReader::get_entry_by_id(uint32_t id) const {
    for (const auto& entry : pup_info_.entries) {
        if (entry.id == id) {
            return &entry;
        }
    }
    return nullptr;
}

bool PUPReader::extract_entry(uint32_t id, const std::string& output_path) {
    const PUPEntry* entry = get_entry_by_id(id);
    if (!entry) {
        Logger::log_error("[PUPReader] Entry with ID 0x" + std::to_string(id) + " not found");
        return false;
    }
    
    if (!file_stream_.is_open()) {
        Logger::log_error("[PUPReader] PUP file not open");
        return false;
    }
    
    // Seek to entry offset
    file_stream_.seekg(entry->offset);
    if (!file_stream_) {
        Logger::log_error("[PUPReader] Failed to seek to entry offset");
        return false;
    }
    
    // Open output file
    std::ofstream output(output_path, std::ios::binary);
    if (!output) {
        Logger::log_error("[PUPReader] Failed to create output file: " + output_path);
        return false;
    }
    
    // Copy data
    const size_t buffer_size = 64 * 1024; // 64KB buffer
    std::vector<char> buffer(buffer_size);
    uint64_t remaining = entry->size;
    
    while (remaining > 0) {
        size_t to_read = std::min(static_cast<uint64_t>(buffer_size), remaining);
        file_stream_.read(buffer.data(), to_read);
        
        if (!file_stream_) {
            Logger::log_error("[PUPReader] Failed to read entry data");
            return false;
        }
        
        output.write(buffer.data(), to_read);
        if (!output) {
            Logger::log_error("[PUPReader] Failed to write output data");
            return false;
        }
        
        remaining -= to_read;
    }
    
    Logger::log_info("[PUPReader] Successfully extracted entry 0x" + 
                    std::to_string(id) + " to " + output_path);
    return true;
}

bool PUPReader::extract_all(const std::string& output_dir) {
    if (!pup_info_.is_valid) {
        Logger::log_error("[PUPReader] No valid PUP file loaded");
        return false;
    }
    
    // Create output directory
    std::filesystem::create_directories(output_dir);
    
    bool success = true;
    for (const auto& entry : pup_info_.entries) {
        std::string filename = "entry_0x" + std::to_string(entry.id) + ".bin";
        std::string output_path = output_dir + "/" + filename;
        
        if (!extract_entry(entry.id, output_path)) {
            success = false;
        }
    }
    
    return success;
}

std::string PUPReader::get_entry_description(uint32_t id) const {
    auto it = entry_descriptions_.find(id);
    if (it != entry_descriptions_.end()) {
        return it->second;
    }
    return "Unknown Entry";
}

bool PUPReader::validate_integrity() {
    if (!pup_info_.is_valid) {
        return false;
    }
    
    // Basic integrity checks
    for (const auto& entry : pup_info_.entries) {
        if (entry.size == 0) {
            Logger::log_warn("[PUPReader] Entry 0x" + std::to_string(entry.id) + " has zero size");
        }
        
        // Check if offset is reasonable
        if (entry.offset < 24 + (pup_info_.file_count * 24)) {
            Logger::log_error("[PUPReader] Entry 0x" + std::to_string(entry.id) + " has invalid offset");
            return false;
        }
    }
    
    return true;
}

std::string PUPReader::get_version_string() const {
    if (!pup_info_.is_valid) {
        return "Unknown";
    }
    
    // Convert version to readable format
    uint32_t major = (pup_info_.version >> 32) & 0xFFFF;
    uint32_t minor = (pup_info_.version >> 16) & 0xFFFF;
    uint32_t patch = pup_info_.version & 0xFFFF;
    
    return std::to_string(major) + "." + std::to_string(minor) + "." + std::to_string(patch);
}

} // namespace Recovery