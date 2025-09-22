#pragma once

#include <string>
#include <vector>
#include <cstdint>
#include <fstream>

namespace Recovery {

// PUP Entry Structure (based on tests/pupreader.cpp)
struct PUPEntry {
    uint32_t id;
    uint64_t offset;
    uint64_t size;
    std::string description; // Optional description for known IDs
};

// PUP File Information
struct PUPFileInfo {
    std::string file_path;
    uint64_t version;
    uint64_t file_count;
    std::vector<PUPEntry> entries;
    bool is_valid;
};

// PUP Reader Class - Integrates existing pupreader.cpp logic
class PUPReader {
public:
    PUPReader();
    ~PUPReader();

    // Read and parse PUP file
    bool read_pup_file(const std::string& file_path);

    // Get PUP file information
    const PUPFileInfo& get_pup_info() const { return pup_info_; }

    // Check if PUP is valid
    bool is_valid() const { return pup_info_.is_valid; }

    // Get specific entry by ID
    const PUPEntry* get_entry_by_id(uint32_t id) const;

    // Extract entry to file
    bool extract_entry(uint32_t id, const std::string& output_path);

    // Extract all entries to directory
    bool extract_all(const std::string& output_dir);

    // Get entry description (for known IDs)
    std::string get_entry_description(uint32_t id) const;

    // Validate PUP integrity
    bool validate_integrity();

    // Get PUP version string
    std::string get_version_string() const;

private:
    PUPFileInfo pup_info_;
    std::ifstream file_stream_;

    // Initialize known entry descriptions
    void initialize_entry_descriptions();
    
    // Known PUP entry descriptions
    std::map<uint32_t, std::string> entry_descriptions_;

    // Read PUP header (magic, version, file count)
    bool read_header();

    // Read PUP entries table
    bool read_entries();

    // Validate magic header
    bool validate_magic(const char* magic) const;
};

} // namespace Recovery