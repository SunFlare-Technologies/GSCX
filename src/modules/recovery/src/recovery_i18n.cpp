#include "recovery_i18n.h"
#include <array>

namespace gscx {
namespace recovery {

Language I18n::current_lang_ = Language::ENGLISH;

const std::unordered_map<std::string, std::array<const char*, 3>> I18n::translations_ = {
    // Format: {key, {English, Spanish, Portuguese}}
    {"recovery.init", {"Recovery Mode initialized", "Modo Recovery inicializado", "Modo Recovery inicializado"}},
    {"recovery.menu", {"Recovery Menu", "Menú de Recovery", "Menu de Recovery"}},
    {"recovery.pup_detected", {"PUP file detected. Size: %lld bytes", "Archivo PUP detectado. Tamaño: %lld bytes", "Arquivo PUP detectado. Tamanho: %lld bytes"}},
    {"recovery.pup_missing", {"No PUP file specified via GSCX_RECOVERY_PUP. Waiting for USB device...", "No se especificó archivo PUP via GSCX_RECOVERY_PUP. Esperando dispositivo USB...", "Nenhum arquivo PUP especificado via GSCX_RECOVERY_PUP. Aguardando dispositivo USB..."}},
    {"recovery.pup_invalid", {"GSCX_RECOVERY_PUP variable set, but file could not be opened.", "Variable GSCX_RECOVERY_PUP configurada, pero el archivo no pudo ser abierto.", "Variável GSCX_RECOVERY_PUP configurada, mas o arquivo não pôde ser aberto."}},
    {"recovery.nand_check", {"HLE: basic initialization, checking NAND/flash...", "HLE: inicialización básica, verificando NAND/flash...", "HLE: inicialização básica, verificando NAND/flash..."}},
    {"recovery.flash_check", {"Flash integrity check completed", "Verificación de integridad del flash completada", "Verificação de integridade do flash concluída"}},
    {"recovery.system_init", {"System initialization complete", "Inicialización del sistema completa", "Inicialização do sistema concluída"}},
    {"recovery.bootloader", {"Bootloader started", "Bootloader iniciado", "Bootloader iniciado"}},
    {"recovery.power_on", {"Console powered ON", "Consola ENCENDIDA", "Console LIGADO"}},
    {"recovery.power_off", {"Console powered OFF", "Consola APAGADA", "Console DESLIGADO"}},
    {"recovery.disc_eject", {"Disc ejected", "Disco expulsado", "Disco ejetado"}},
    {"recovery.disc_insert", {"Disc inserted", "Disco insertado", "Disco inserido"}},
    {"recovery.iso_load", {"ISO file loaded: %s", "Archivo ISO cargado: %s", "Arquivo ISO carregado: %s"}},
    {"recovery.iso_invalid", {"Invalid ISO file: %s", "Archivo ISO inválido: %s", "Arquivo ISO inválido: %s"}},
    {"recovery.ee_init", {"Emotion Engine (EE) initialized for backward compatibility", "Emotion Engine (EE) inicializado para retrocompatibilidad", "Emotion Engine (EE) inicializado para retrocompatibilidade"}},
    {"recovery.ee_compat", {"EE compatibility mode: %s", "Modo de compatibilidad EE: %s", "Modo de compatibilidade EE: %s"}},
    {"recovery.menu_title", {"PS3 Recovery Menu", "Menú de Recovery PS3", "Menu de Recovery PS3"}},
    {"recovery.menu_install", {"Install System Software", "Instalar Software del Sistema", "Instalar Software do Sistema"}},
    {"recovery.menu_restore", {"Restore PS3 System", "Restaurar Sistema PS3", "Restaurar Sistema PS3"}},
    {"recovery.menu_format", {"Format Hard Disk", "Formatear Disco Duro", "Formatar Disco Rígido"}},
    {"recovery.menu_exit", {"Exit Recovery Mode", "Salir del Modo Recovery", "Sair do Modo Recovery"}}
};

void I18n::set_language(Language lang) {
    current_lang_ = lang;
}

Language I18n::get_language() {
    return current_lang_;
}

const char* I18n::t(const char* key) {
    auto it = translations_.find(key);
    if (it != translations_.end()) {
        return it->second[static_cast<int>(current_lang_)];
    }
    return key; // Fallback to key if translation not found
}

} // namespace recovery
} // namespace gscx