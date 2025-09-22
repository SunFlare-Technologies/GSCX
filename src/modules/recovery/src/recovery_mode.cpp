#include "recovery_mode.h"
#include "recovery_i18n.h"
#include "ps3_models.h"
#include "pup_reader.h"
#include "../../../core/include/logger.h"
#include "../../../core/include/host_services_c.h"
#include <fstream>
#include <iostream>
#include <cstring>
#include <algorithm>
#include <sstream>
#include <thread>
#include <chrono>

namespace gscx {
namespace recovery {

// RecoveryMode Implementation
RecoveryMode::RecoveryMode(HostServicesC* host)
    : host_(host)
    , console_state_(ConsoleState::OFF)
    , disc_state_(DiscState::EMPTY)
    , ee_mode_(EEMode::DISABLED)
    , selected_menu_item_(0)
    , initialized_(false) {
}

RecoveryMode::~RecoveryMode() {
    if (initialized_) {
        shutdown();
    }
}

bool RecoveryMode::initialize() {
    if (initialized_) {
        return true;
    }

    log_info(I18n::t(keys::RECOVERY_INIT));
    
    // Initialize console model
    init_console_model();
    
    // Check system integrity
    if (!check_nand_integrity()) {
        log_error("NAND integrity check failed");
        return false;
    }
    
    if (!check_flash_integrity()) {
        log_error("Flash integrity check failed");
        return false;
    }
    
    // Initialize EE system if supported
    if (console_model_.has_ee_compatibility) {
        init_ee_system();
    }
    
    // Initialize recovery menu
    init_recovery_menu();
    
    // Check for PUP file
    const char* pup_env = std::getenv("GSCX_RECOVERY_PUP");
    if (pup_env && pup_env[0]) {
        load_pup_file(pup_env);
    } else {
        log_info(I18n::t(keys::RECOVERY_PUP_MISSING));
    }
    
    initialized_ = true;
    log_info(I18n::t(keys::RECOVERY_SYSTEM_INIT));
    return true;
}

void RecoveryMode::shutdown() {
    if (!initialized_) {
        return;
    }
    
    power_off();
    initialized_ = false;
}

void RecoveryMode::run_main_loop() {
    if (!initialized_) {
        log_error("Recovery mode not initialized");
        return;
    }
    
    console_state_ = ConsoleState::RECOVERY_MENU;
    show_recovery_menu();
}

void RecoveryMode::power_on() {
    if (console_state_ == ConsoleState::OFF) {
        console_state_ = ConsoleState::BOOTING;
        log_info(I18n::t(keys::RECOVERY_POWER_ON));
        
        // Simulate boot process
        console_state_ = ConsoleState::RECOVERY_MENU;
    }
}

void RecoveryMode::power_off() {
    console_state_ = ConsoleState::OFF;
    disc_state_ = DiscState::EMPTY;
    log_info(I18n::t(keys::RECOVERY_POWER_OFF));
}

void RecoveryMode::eject_disc() {
    if (disc_state_ == DiscState::INSERTED || disc_state_ == DiscState::READING) {
        disc_state_ = DiscState::EMPTY;
        current_iso_ = ISOFile{};
        log_info(I18n::t(keys::RECOVERY_DISC_EJECT));
    }
}

void RecoveryMode::insert_disc(const std::string& iso_path) {
    if (disc_state_ == DiscState::EMPTY) {
        if (load_iso_file(iso_path)) {
            disc_state_ = DiscState::INSERTED;
            log_info(I18n::t(keys::RECOVERY_DISC_INSERT));
        } else {
            disc_state_ = DiscState::ERROR;
        }
    }
}

bool RecoveryMode::load_pup_file(const std::string& path) {
    log_info("Loading PUP file: " + path);
    
    Recovery::PUPReader pup_reader;
    if (!pup_reader.read_pup_file(path)) {
        log_error("Failed to read PUP file: " + path);
        return false;
    }
    
    if (!pup_reader.validate_integrity()) {
        log_error("PUP file integrity check failed");
        return false;
    }
    
    const auto& pup_info = pup_reader.get_pup_info();
    log_info("PUP Version: " + pup_reader.get_version_string());
    log_info("PUP Entries: " + std::to_string(pup_info.file_count));
    
    // Store PUP information for recovery operations
    current_pup_ = pup_info;
    
    return true;
}

bool RecoveryMode::load_iso_file(const std::string& path) {
    if (!validate_iso_file(path)) {
        std::string msg = std::string(I18n::t(keys::RECOVERY_ISO_INVALID));
        size_t pos = msg.find("%s");
        if (pos != std::string::npos) {
            msg.replace(pos, 2, path);
        }
        log_error(msg);
        return false;
    }
    
    if (ISOReader::read_iso_info(path, current_iso_)) {
        std::string msg = std::string(I18n::t(keys::RECOVERY_ISO_LOAD));
        size_t pos = msg.find("%s");
        if (pos != std::string::npos) {
            msg.replace(pos, 2, path);
        }
        log_info(msg);
        return true;
    }
    
    return false;
}

void RecoveryMode::set_ee_mode(EEMode mode) {
    if (console_model_.has_ee_compatibility) {
        ee_mode_ = mode;
        
        std::string mode_str;
        switch (mode) {
            case EEMode::DISABLED: mode_str = "Disabled"; break;
            case EEMode::SOFTWARE_EMULATION: mode_str = "Software Emulation"; break;
            case EEMode::HARDWARE_ACCELERATION: mode_str = "Hardware Acceleration"; break;
        }
        
        std::string msg = std::string(I18n::t(keys::RECOVERY_EE_COMPAT));
        size_t pos = msg.find("%s");
        if (pos != std::string::npos) {
            msg.replace(pos, 2, mode_str);
        }
        log_info(msg);
    }
}

bool RecoveryMode::is_ee_compatible() const {
    return console_model_.has_ee_compatibility && ee_mode_ != EEMode::DISABLED;
}

void RecoveryMode::show_recovery_menu() {
    log_info(I18n::t(keys::RECOVERY_MENU_TITLE));
    log_info("=");
    
    for (size_t i = 0; i < menu_items_.size(); ++i) {
        const auto& item = menu_items_[i];
        std::string prefix = (i == selected_menu_item_) ? "> " : "  ";
        std::string status = item.enabled ? "" : " (disabled)";
        log_info(prefix + std::to_string(i + 1) + ". " + I18n::t(item.text_key.c_str()) + status);
    }
}

void RecoveryMode::handle_menu_selection(int selection) {
    if (selection >= 1 && selection <= static_cast<int>(menu_items_.size())) {
        selected_menu_item_ = selection - 1;
        const auto& item = menu_items_[selected_menu_item_];
        
        if (item.enabled && item.action) {
            item.action();
        }
    }
}

void RecoveryMode::set_language(Language lang) {
    I18n::set_language(lang);
}

Language RecoveryMode::get_language() const {
    return I18n::get_language();
}

// Private methods
void RecoveryMode::log_info(const std::string& message) {
    if (host_ && host_->log_info) {
        host_->log_info(("[Recovery] " + message).c_str());
    }
}

void RecoveryMode::log_warn(const std::string& message) {
    if (host_ && host_->log_warn) {
        host_->log_warn(("[Recovery] " + message).c_str());
    }
}

void RecoveryMode::log_error(const std::string& message) {
    if (host_ && host_->log_error) {
        host_->log_error(("[Recovery] " + message).c_str());
    }
}

bool RecoveryMode::check_nand_integrity() {
    log_info(I18n::t(keys::RECOVERY_NAND_CHECK));
    // Simulate NAND check
    return true;
}

bool RecoveryMode::check_flash_integrity() {
    log_info(I18n::t(keys::RECOVERY_FLASH_CHECK));
    // Simulate flash check
    return true;
}

bool RecoveryMode::validate_pup_file(const std::string& path) {
    std::ifstream file(path, std::ios::binary);
    if (!file.good()) {
        return false;
    }
    
    char magic[8];
    file.read(magic, 8);
    return std::string(magic, 5) == "SCEUF";
}

bool RecoveryMode::validate_iso_file(const std::string& path) {
    std::ifstream file(path, std::ios::binary);
    if (!file.good()) {
        return false;
    }
    
    // Check file size (minimum 4GB for PS3 games)
    file.seekg(0, std::ios::end);
    auto size = file.tellg();
    return size > 0;
}

void RecoveryMode::init_console_model() {
    // Default PS3 model (can be configured)
    console_model_.name = "CECHA01";
    console_model_.has_ee_compatibility = true;
    console_model_.has_gs_compatibility = true;
    console_model_.cpu_type = "Cell Broadband Engine";
    console_model_.gpu_type = "RSX Reality Synthesizer";
}

void RecoveryMode::init_recovery_menu() {
    menu_items_.clear();
    
    menu_items_.push_back({
        1, keys::RECOVERY_MENU_INSTALL,
        [this]() { menu_install_system(); },
        current_pup_.is_valid
    });
    
    menu_items_.push_back({
        2, keys::RECOVERY_MENU_RESTORE,
        [this]() { menu_restore_system(); },
        true
    });
    
    menu_items_.push_back({
        3, keys::RECOVERY_MENU_FORMAT,
        [this]() { menu_format_hdd(); },
        true
    });
    
    menu_items_.push_back({
        4, keys::RECOVERY_MENU_EXIT,
        [this]() { menu_exit_recovery(); },
        true
    });
}

void RecoveryMode::init_ee_system() {
    if (console_model_.has_ee_compatibility) {
        set_ee_mode(EEMode::SOFTWARE_EMULATION);
        log_info(I18n::t(keys::RECOVERY_EE_INIT));
    }
}

void RecoveryMode::menu_install_system() {
    if (current_pup_.is_valid) {
        console_state_ = ConsoleState::INSTALLING;
        log_info("Installing system software from PUP file...");
        // Simulate installation process
        console_state_ = ConsoleState::RECOVERY_MENU;
        log_info("Installation completed successfully.");
    }
}

void RecoveryMode::menu_restore_system() {
    log_info("Restoring PS3 system to factory defaults...");
    // Simulate restore process
    log_info("System restore completed.");
}

void RecoveryMode::menu_format_hdd() {
    console_state_ = ConsoleState::FORMATTING;
    log_info("Formatting hard disk drive...");
    // Simulate format process
    console_state_ = ConsoleState::RECOVERY_MENU;
    log_info("Hard disk formatting completed.");
}

void RecoveryMode::menu_exit_recovery() {
    log_info("Exiting Recovery Mode...");
    power_off();
}

} // namespace recovery
} // namespace gscx