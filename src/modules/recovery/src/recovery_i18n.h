#pragma once
#include <string>
#include <unordered_map>

namespace gscx {
namespace recovery {

enum class Language {
    ENGLISH = 0,
    SPANISH = 1,
    PORTUGUESE = 2
};

class I18n {
public:
    static void set_language(Language lang);
    static Language get_language();
    static const char* t(const char* key);
    
private:
    static Language current_lang_;
    static const std::unordered_map<std::string, std::array<const char*, 3>> translations_;
};

// Translation keys
namespace keys {
    constexpr const char* RECOVERY_INIT = "recovery.init";
    constexpr const char* RECOVERY_MENU = "recovery.menu";
    constexpr const char* RECOVERY_PUP_DETECTED = "recovery.pup_detected";
    constexpr const char* RECOVERY_PUP_MISSING = "recovery.pup_missing";
    constexpr const char* RECOVERY_PUP_INVALID = "recovery.pup_invalid";
    constexpr const char* RECOVERY_NAND_CHECK = "recovery.nand_check";
    constexpr const char* RECOVERY_FLASH_CHECK = "recovery.flash_check";
    constexpr const char* RECOVERY_SYSTEM_INIT = "recovery.system_init";
    constexpr const char* RECOVERY_BOOTLOADER = "recovery.bootloader";
    constexpr const char* RECOVERY_POWER_ON = "recovery.power_on";
    constexpr const char* RECOVERY_POWER_OFF = "recovery.power_off";
    constexpr const char* RECOVERY_DISC_EJECT = "recovery.disc_eject";
    constexpr const char* RECOVERY_DISC_INSERT = "recovery.disc_insert";
    constexpr const char* RECOVERY_ISO_LOAD = "recovery.iso_load";
    constexpr const char* RECOVERY_ISO_INVALID = "recovery.iso_invalid";
    constexpr const char* RECOVERY_EE_INIT = "recovery.ee_init";
    constexpr const char* RECOVERY_EE_COMPAT = "recovery.ee_compat";
    constexpr const char* RECOVERY_MENU_TITLE = "recovery.menu_title";
    constexpr const char* RECOVERY_MENU_INSTALL = "recovery.menu_install";
    constexpr const char* RECOVERY_MENU_RESTORE = "recovery.menu_restore";
    constexpr const char* RECOVERY_MENU_FORMAT = "recovery.menu_format";
    constexpr const char* RECOVERY_MENU_EXIT = "recovery.menu_exit";
}

} // namespace recovery
} // namespace gscx