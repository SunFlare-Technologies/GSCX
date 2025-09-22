#include "ps3_models.h"
#include "../../../core/include/logger.h"
#include <algorithm>

namespace Recovery {

// Global model database instance
PS3ModelDatabase g_model_database;

PS3ModelDatabase::PS3ModelDatabase() {
    initialize();
}

void PS3ModelDatabase::initialize() {
    Logger::log_info("[Recovery] Initializing PS3 Model Database...");
    
    load_fat_models();
    load_slim_models();
    load_super_slim_models();
    
    Logger::log_info("[Recovery] PS3 Model Database initialized with " + std::to_string(models_.size()) + " models");
}

void PS3ModelDatabase::load_fat_models() {
    // Fat models (2006-2009)
    models_["CECHA01"] = {"CECHA01", 2006, "60 GB", {"Blu-ray", "DVD", "CD"}, true, "fat"};
    models_["CECHB01"] = {"CECHB01", 2006, "20 GB", {"Blu-ray", "DVD", "CD"}, true, "fat"};
    models_["CECHC01"] = {"CECHC01", 2007, "60 GB", {"Blu-ray", "DVD", "CD"}, true, "fat"};
    models_["CECHG01"] = {"CECHG01", 2007, "80 GB", {"Blu-ray", "DVD", "CD"}, true, "fat"};
    models_["CECHH01"] = {"CECHH01", 2007, "40 GB", {"Blu-ray", "DVD", "CD"}, false, "fat"};
    models_["CECHJ01"] = {"CECHJ01", 2008, "80 GB", {"Blu-ray", "DVD", "CD"}, false, "fat"};
    models_["CECHK01"] = {"CECHK01", 2008, "40 GB", {"Blu-ray", "DVD", "CD"}, false, "fat"};
    models_["CECHL01"] = {"CECHL01", 2008, "80 GB", {"Blu-ray", "DVD", "CD"}, false, "fat"};
    models_["CECHM01"] = {"CECHM01", 2008, "40 GB", {"Blu-ray", "DVD", "CD"}, false, "fat"};
    models_["CECHN01"] = {"CECHN01", 2008, "80 GB", {"Blu-ray", "DVD", "CD"}, false, "fat"};
    models_["CECHP01"] = {"CECHP01", 2009, "80 GB", {"Blu-ray", "DVD", "CD"}, false, "fat"};
    models_["CECHQ01"] = {"CECHQ01", 2009, "80 GB", {"Blu-ray", "DVD", "CD"}, false, "fat"};
}

void PS3ModelDatabase::load_slim_models() {
    // Slim models (2009-2012)
    models_["CECH2001A"] = {"CECH2001A", 2009, "120 GB", {"Blu-ray", "DVD", "CD"}, false, "slim"};
    models_["CECH2001B"] = {"CECH2001B", 2009, "250 GB", {"Blu-ray", "DVD", "CD"}, false, "slim"};
    models_["CECH2101A"] = {"CECH2101A", 2010, "120 GB", {"Blu-ray", "DVD", "CD"}, false, "slim"};
    models_["CECH2101B"] = {"CECH2101B", 2010, "250 GB", {"Blu-ray", "DVD", "CD"}, false, "slim"};
    models_["CECH2501A"] = {"CECH2501A", 2010, "160 GB", {"Blu-ray", "DVD", "CD"}, false, "slim"};
    models_["CECH2501B"] = {"CECH2501B", 2010, "320 GB", {"Blu-ray", "DVD", "CD"}, false, "slim"};
    models_["CECH3001A"] = {"CECH3001A", 2010, "160 GB", {"Blu-ray", "DVD", "CD"}, false, "slim"};
    models_["CECH3001B"] = {"CECH3001B", 2010, "320 GB", {"Blu-ray", "DVD", "CD"}, false, "slim"};
    models_["CECH3004A"] = {"CECH3004A", 2011, "160 GB", {"Blu-ray", "DVD", "CD"}, false, "slim"};
    models_["CECH3004B"] = {"CECH3004B", 2011, "320 GB", {"Blu-ray", "DVD", "CD"}, false, "slim"};
}

void PS3ModelDatabase::load_super_slim_models() {
    // Super Slim models (2012-2017)
    models_["CECH4001A"] = {"CECH4001A", 2012, "12 GB", {"Blu-ray", "DVD", "CD"}, false, "super_slim"};
    models_["CECH4001B"] = {"CECH4001B", 2012, "250 GB", {"Blu-ray", "DVD", "CD"}, false, "super_slim"};
    models_["CECH4001C"] = {"CECH4001C", 2012, "500 GB", {"Blu-ray", "DVD", "CD"}, false, "super_slim"};
    models_["CECH4201A"] = {"CECH4201A", 2012, "12 GB", {"Blu-ray", "DVD", "CD"}, false, "super_slim"};
    models_["CECH4201B"] = {"CECH4201B", 2012, "250 GB", {"Blu-ray", "DVD", "CD"}, false, "super_slim"};
    models_["CECH4201C"] = {"CECH4201C", 2012, "500 GB", {"Blu-ray", "DVD", "CD"}, false, "super_slim"};
    models_["CECH4301A"] = {"CECH4301A", 2013, "12 GB", {"Blu-ray", "DVD", "CD"}, false, "super_slim"};
    models_["CECH4301B"] = {"CECH4301B", 2013, "250 GB", {"Blu-ray", "DVD", "CD"}, false, "super_slim"};
    models_["CECH4301C"] = {"CECH4301C", 2013, "500 GB", {"Blu-ray", "DVD", "CD"}, false, "super_slim"};
}

const PS3ModelInfo* PS3ModelDatabase::get_model_info(const std::string& model_id) const {
    auto it = models_.find(model_id);
    if (it != models_.end()) {
        return &it->second;
    }
    return nullptr;
}

bool PS3ModelDatabase::supports_retrocompatibility(const std::string& model_id) const {
    const PS3ModelInfo* info = get_model_info(model_id);
    return info ? info->retrocompatibility : false;
}

std::vector<PS3ModelInfo> PS3ModelDatabase::get_models_by_generation(const std::string& generation) const {
    std::vector<PS3ModelInfo> result;
    for (const auto& pair : models_) {
        if (pair.second.generation == generation) {
            result.push_back(pair.second);
        }
    }
    return result;
}

std::vector<PS3ModelInfo> PS3ModelDatabase::get_retrocompatible_models() const {
    std::vector<PS3ModelInfo> result;
    for (const auto& pair : models_) {
        if (pair.second.retrocompatibility) {
            result.push_back(pair.second);
        }
    }
    return result;
}

std::string PS3ModelDatabase::detect_current_model() const {
    // In a real implementation, this would read from system EEPROM/NAND
    // For now, we'll default to a retrocompatible model for testing
    Logger::log_info("[Recovery] Model detection: defaulting to CECHA01 (60GB Fat - Retrocompatible)");
    return "CECHA01";
}

} // namespace Recovery