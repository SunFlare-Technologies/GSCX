#pragma once

#include <string>
#include <vector>
#include <unordered_map>

namespace Recovery {

// PS3 Model Information Structure
struct PS3ModelInfo {
    std::string model_id;
    int year;
    std::string storage;
    std::vector<std::string> media;
    bool retrocompatibility;
    std::string generation; // "fat", "slim", "super_slim"
};

// PS3 Model Database Class
class PS3ModelDatabase {
public:
    PS3ModelDatabase();
    ~PS3ModelDatabase() = default;

    // Initialize model database
    void initialize();

    // Get model information by ID
    const PS3ModelInfo* get_model_info(const std::string& model_id) const;

    // Check if model supports retrocompatibility
    bool supports_retrocompatibility(const std::string& model_id) const;

    // Get all models by generation
    std::vector<PS3ModelInfo> get_models_by_generation(const std::string& generation) const;

    // Get all retrocompatible models
    std::vector<PS3ModelInfo> get_retrocompatible_models() const;

    // Detect model from system information
    std::string detect_current_model() const;

private:
    std::unordered_map<std::string, PS3ModelInfo> models_;
    void load_fat_models();
    void load_slim_models();
    void load_super_slim_models();
};

// Global model database instance
extern PS3ModelDatabase g_model_database;

} // namespace Recovery