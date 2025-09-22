#pragma once
#include "recovery_i18n.h"
#include "host_services_c.h"
#include "ps3_models.h"
#include "pup_reader.h"
#include <string>
#include <vector>
#include <memory>
#include <functional>

namespace gscx {
namespace recovery {

// PS3 Console State
enum class ConsoleState {
    OFF,
    BOOTING,
    RECOVERY_MENU,
    INSTALLING,
    FORMATTING,
    ERROR
};

// Disc State
enum class DiscState {
    EMPTY,
    INSERTED,
    READING,
    ERROR
};

// EE (Emotion Engine) Compatibility Mode
enum class EEMode {
    DISABLED,
    SOFTWARE_EMULATION,
    HARDWARE_ACCELERATION
};

// Use PUP structures from Recovery namespace
using PUPEntry = Recovery::PUPEntry;
using PUPFile = Recovery::PUPFileInfo;

// ISO File Structure
struct ISOFile {
    std::string path;
    uint64_t size;
    std::string title;
    bool is_valid;
};

// Console Model Info
struct ConsoleModel {
    std::string name;
    bool has_ee_compatibility;
    bool has_gs_compatibility;
    std::string cpu_type;
    std::string gpu_type;
};

// Recovery Menu Item
struct MenuItem {
    int id;
    std::string text_key;
    std::function<void()> action;
    bool enabled;
};

// Main Recovery Mode Class
class RecoveryMode {
public:
    RecoveryMode(HostServicesC* host);
    ~RecoveryMode();

    // Core functions
    bool initialize();
    void shutdown();
    void run_main_loop();

    // Console control
    void power_on();
    void power_off();
    ConsoleState get_console_state() const { return console_state_; }

    // Disc control
    void eject_disc();
    void insert_disc(const std::string& iso_path);
    DiscState get_disc_state() const { return disc_state_; }

    // PUP handling
    bool load_pup_file(const std::string& path);
    const PUPFile& get_current_pup() const { return current_pup_; }

    // ISO handling
    bool load_iso_file(const std::string& path);
    const ISOFile& get_current_iso() const { return current_iso_; }

    // EE compatibility
    void set_ee_mode(EEMode mode);
    EEMode get_ee_mode() const { return ee_mode_; }
    bool is_ee_compatible() const;

    // Recovery menu
    void show_recovery_menu();
    void handle_menu_selection(int selection);

    // Language support
    void set_language(Language lang);
    Language get_language() const;

private:
    // Internal functions
    void log_info(const std::string& message);
    void log_warn(const std::string& message);
    void log_error(const std::string& message);

    bool check_nand_integrity();
    bool check_flash_integrity();
    bool validate_pup_file(const std::string& path);
    bool validate_iso_file(const std::string& path);
    
    void init_console_model();
    void init_recovery_menu();
    void init_ee_system();

    // Menu actions
    void menu_install_system();
    void menu_restore_system();
    void menu_format_hdd();
    void menu_exit_recovery();

    // Member variables
    HostServicesC* host_;
    ConsoleState console_state_;
    DiscState disc_state_;
    EEMode ee_mode_;
    
    PUPFile current_pup_;
    ISOFile current_iso_;
    ConsoleModel console_model_;
    
    std::vector<MenuItem> menu_items_;
    int selected_menu_item_;
    
    bool initialized_;
};

// Bootloader class
class Bootloader {
public:
    Bootloader(HostServicesC* host);
    ~Bootloader();

    bool initialize();
    void shutdown();
    bool boot_recovery_mode();
    bool boot_system_software();

private:
    HostServicesC* host_;
    bool initialized_;
    
    void log_info(const std::string& message);
    void log_warn(const std::string& message);
    void log_error(const std::string& message);
};

// PUP Reader utility (integration with existing pupreader)
class PUPReader {
public:
    static bool read_pup_info(const std::string& path, PUPFile& pup_info);
    static bool extract_entry(const std::string& pup_path, uint32_t entry_id, const std::string& output_path);
    static std::vector<PUPEntry> list_entries(const std::string& path);

private:
    static bool validate_magic(const std::string& path);
};

// ISO Reader utility
class ISOReader {
public:
    static bool read_iso_info(const std::string& path, ISOFile& iso_info);
    static bool mount_iso(const std::string& path);
    static void unmount_iso();
    static std::string get_iso_title(const std::string& path);

private:
    static bool validate_iso_format(const std::string& path);
};

} // namespace recovery
} // namespace gscx