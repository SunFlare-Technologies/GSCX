import os
import ctypes
from typing import Callable, Optional
import struct
import tempfile
import shutil
from ctypes import CFUNCTYPE, WINFUNCTYPE, c_char_p, c_void_p, c_bool
from .i18n import t  # added

MODULES = [
    "gscx_cpu_cell",
    "gscx_gpu_rsx",
    "gscx_recovery",
    "gscx_bootloader",
    "gscx_syscon",
    "gscx_hypervisor",
]

ENTRY_GETINFO = b"GSCX_GetModuleInfo"
ENTRY_INIT = b"GSCX_Initialize"
ENTRY_SHUT = b"GSCX_Shutdown"

# Em host_services_c.h, GSCX_CALL = __stdcall no Windows
LOG_FN = WINFUNCTYPE(None, c_char_p) if hasattr(ctypes, 'WINFUNCTYPE') else CFUNCTYPE(None, c_char_p)

# Bridge para encaminhar logs do nativo -> console e GUI
class _LogBridge:
    target: Callable[[str], None] | None = None

    @staticmethod
    def handle(msg_bytes):
        try:
            s = msg_bytes.decode('utf-8')
        except Exception:
            s = str(msg_bytes)
        # Console
        print(s, end='')
        # GUI
        if _LogBridge.target:
            try:
                _LogBridge.target(s)
            except Exception:
                pass

INFO_CB = LOG_FN(_LogBridge.handle)
WARN_CB = LOG_FN(_LogBridge.handle)
ERR_CB  = LOG_FN(_LogBridge.handle)

class HostServices(ctypes.Structure):
    _fields_ = [
        ("log_info", LOG_FN),
        ("log_warn", LOG_FN),
        ("log_error", LOG_FN),
    ]

class ModulesLoader:
    def __init__(self, on_log: Callable[[str], None]):
        self.on_log = on_log
        # Última pasta de USB virtual utilizada
        self.last_usb_dir: Optional[str] = None
        # Último caminho de HDD virtual alocado
        self.last_hdd_path: Optional[str] = None
        # Configura o destino do bridge para que os logs nativos apareçam na GUI
        _LogBridge.target = on_log
        self.loaded = []
        self._temp_dir = None
        self._vusb_dir = None  # pasta temporária para 'pendrive virtual'

    def _log(self, msg: str):
        if self.on_log:
            self.on_log(msg)

    def _host_services(self) -> HostServices:
        return HostServices(INFO_CB, WARN_CB, ERR_CB)

    def _load_from_dirs(self, dirs):
        dll_names = [m + ".dll" for m in MODULES]
        for d in dirs:
            for dll in dll_names:
                path = os.path.join(d, dll)
                if not os.path.isfile(path):
                    continue
                try:
                    lib = ctypes.WinDLL(path)
                    self._log(t('modules.loaded', path=path))
                    # Opcional: invocar GSCX_GetModuleInfo
                    try:
                        get_info = getattr(lib, ENTRY_GETINFO.decode())
                        get_info.restype = None
                    except AttributeError:
                        self._log(t('modules.entrypoint_missing', entry=ENTRY_GETINFO.decode(), dll=dll))
                    # Inicializar
                    try:
                        init = getattr(lib, ENTRY_INIT.decode())
                        init.argtypes = [c_void_p]
                        init.restype = c_bool
                        hs = self._host_services()
                        ok = init(ctypes.byref(hs))
                        self._log(t('modules.initialize_returned', ok=ok))
                    except AttributeError:
                        self._log(t('modules.entrypoint_missing', entry=ENTRY_INIT.decode(), dll=dll))
                    self.loaded.append((dll, lib))
                except OSError as e:
                    self._log(t('modules.load_failed', path=path, error=e))

    def load_default_modules(self):
        # Tenta localizar DLLs em ./build/bin ou ./bin
        candidates = [
            os.path.abspath(os.path.join(os.getcwd(), "build")),
            os.path.abspath(os.path.join(os.getcwd(), "cpp", "build")),
            os.path.abspath(os.path.join(os.getcwd(), "bin")),
        ]
        found_dirs = [d for d in candidates if os.path.isdir(d)]
        if not found_dirs:
            self._log(t('modules.build_dirs_missing'))
            return
        self._load_from_dirs(found_dirs)

    def load_from_gscore(self, bundle_path: str):
        # Parser simples do formato GSCore (.gscb)
        try:
            with open(bundle_path, 'rb') as f:
                data = f.read()
        except Exception as e:
            self._log(t('modules.bundle_open_fail', error=e))
            return
        # Header: magic(4) ver(2) count(2)
        if len(data) < 8:
            self._log(t('modules.bundle_invalid_header'))
            return
        magic, ver, count = struct.unpack_from('<IHH', data, 0)
        if magic != 0x47534352:
            self._log(t('modules.bundle_magic_invalid'))
            return
        off = 8
        entries = []
        try:
            for _ in range(count):
                type_, name_len = struct.unpack_from('<HH', data, off); off += 4
                name = data[off:off+name_len].decode('utf-8'); off += name_len
                payload_off, size = struct.unpack_from('<II', data, off); off += 8
                entries.append((type_, name, payload_off, size))
        except Exception as e:
            self._log(t('modules.bundle_table_read_error', error=e))
            return
        # Extrair para pasta temporária
        if self._temp_dir:
            try:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            except Exception:
                pass
        self._temp_dir = tempfile.mkdtemp(prefix='gscx_bundle_')
        for type_, name, payload_off, size in entries:
            blob = data[payload_off:payload_off+size]
            out_name = name
            out_path = os.path.join(self._temp_dir, out_name)
            try:
                # garantir subpastas se nome contiver '/'
                os.makedirs(os.path.dirname(out_path), exist_ok=True)
                with open(out_path, 'wb') as wf:
                    wf.write(blob)
                self._log(t('modules.bundle_extracted', name=out_name, size=size))
            except Exception as e:
                self._log(t('modules.bundle_extract_fail', name=out_name, error=e))
        # Carregar módulos a partir da pasta extraída
        self._load_from_dirs([self._temp_dir])

    def boot_recovery(self, pup_path: str | None = None, usb_dir: Optional[str] = None):
        """
        Inicia o módulo de Recovery.
        Se um PUP for fornecido, cria/usa uma pasta de pendrive virtual "usb_dir",
        copia o arquivo como PS3UPDAT.PUP e exporta GSCX_RECOVERY_PUP apontando para ele.
        """
        # Preparar pendrive virtual se PUP informado
        if pup_path:
            try:
                if usb_dir:
                    target_dir = os.path.abspath(usb_dir)
                    os.makedirs(target_dir, exist_ok=True)
                else:
                    # Cria um diretório temporário se não foi fornecido
                    target_dir = tempfile.mkdtemp(prefix="gscx_usb_")
                    # Marcar para limpeza posterior apenas se criado automaticamente
                    self._vusb_dir = target_dir
                dest_file = os.path.join(target_dir, "PS3UPDAT.PUP")
                shutil.copy2(pup_path, dest_file)
                os.environ['GSCX_RECOVERY_PUP'] = dest_file
                self.last_usb_dir = target_dir
                if self.on_log:
                    self.on_log(t('modules.recovery.prepared', path=target_dir))
                    self.on_log(t('modules.recovery.copied', dest=dest_file))
            except Exception as e:
                if self.on_log:
                    self.on_log(t('modules.recovery.prepare_fail', error=e))
                raise
        else:
            # Limpa variável para forçar espera por USB no módulo nativo
            if 'GSCX_RECOVERY_PUP' in os.environ:
                try:
                    del os.environ['GSCX_RECOVERY_PUP']
                except Exception:
                    pass

        try:
            # Procura a DLL de recovery carregada e chama a entry
            for name, lib in self.loaded:
                if name.startswith('gscx_recovery'):
                    try:
                        entry = getattr(lib, 'GSCX_RecoveryEntry')
                        entry.restype = None
                        entry.argtypes = []
                        self._log(t('modules.recovery.calling'))
                        entry()
                        self._log(t('modules.recovery.finished'))
                    except AttributeError:
                        self._log(t('modules.recovery.missing_entry'))
                    break
        finally:
            # Limpeza do pendrive virtual
            if 'GSCX_RECOVERY_PUP' in os.environ:
                try:
                    del os.environ['GSCX_RECOVERY_PUP']
                except Exception:
                    pass
            # Não remover automaticamente a pasta do pendrive virtual (_vusb_dir)
            # para permitir inspeção via botão "Abrir Pasta" na UI. A limpeza
            # ficará sob responsabilidade do usuário ou de uma rotina posterior.
            # if self._vusb_dir:
            #     try:
            #         shutil.rmtree(self._vusb_dir, ignore_errors=True)
            #     except Exception:
            #         pass
            # self._vusb_dir = None

    def unload_all(self):
        for name, lib in self.loaded:
            try:
                shut = getattr(lib, ENTRY_SHUT.decode())
                shut()
            except Exception:
                pass
            self._log(t('modules.unloaded', name=name))
        self.loaded.clear()
        if self._temp_dir:
            try:
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            except Exception:
                pass
            self._temp_dir = None
        # Não remover automaticamente _vusb_dir aqui para permitir inspeção posterior
        # if self._vusb_dir:
        #     try:
        #         shutil.rmtree(self._vusb_dir, ignore_errors=True)
        #     except Exception:
        #         pass
        # self._vusb_dir = None

    def get_last_usb_dir(self) -> Optional[str]:
        return self.last_usb_dir
    
    def boot_lv0_stage(self) -> bool:
        """Inicia o estágio LV0 (Primary Kernel) do bootloader PS3"""
        try:
            self._log("[BOOTLOADER] Iniciando LV0 - Primary Kernel...")
            
            # Procura módulo bootloader carregado
            for name, lib in self.loaded:
                if name.startswith('gscx_bootloader'):
                    try:
                        lv0_entry = getattr(lib, 'GSCX_LV0_Entry')
                        lv0_entry.restype = c_bool
                        lv0_entry.argtypes = []
                        
                        result = lv0_entry()
                        if result:
                            self._log("[LV0] Hardware initialization completed")
                            self._log("[LV0] Security validation passed")
                            self._log("[LV0] Memory setup completed")
                            return True
                        else:
                            self._log("[LV0] Initialization failed")
                            return False
                    except AttributeError:
                        self._log("[LV0] Entry point not found in bootloader module")
                        return False
            
            self._log("[LV0] Bootloader module not loaded")
            return False
            
        except Exception as e:
            self._log(f"[LV0] Error during initialization: {e}")
            return False
    
    def boot_lv1_stage(self) -> bool:
        """Inicia o estágio LV1 (Hypervisor) do bootloader PS3"""
        try:
            self._log("[BOOTLOADER] Iniciando LV1 - Hypervisor...")
            
            # Procura módulo hypervisor carregado
            for name, lib in self.loaded:
                if name.startswith('gscx_hypervisor'):
                    try:
                        lv1_entry = getattr(lib, 'GSCX_LV1_Entry')
                        lv1_entry.restype = c_bool
                        lv1_entry.argtypes = []
                        
                        result = lv1_entry()
                        if result:
                            self._log("[LV1] Hypervisor initialization completed")
                            self._log("[LV1] Virtual memory management active")
                            self._log("[LV1] System services initialized")
                            return True
                        else:
                            self._log("[LV1] Hypervisor initialization failed")
                            return False
                    except AttributeError:
                        self._log("[LV1] Entry point not found in hypervisor module")
                        return False
            
            self._log("[LV1] Hypervisor module not loaded")
            return False
            
        except Exception as e:
            self._log(f"[LV1] Error during hypervisor initialization: {e}")
            return False
    
    def boot_lv2_stage(self) -> bool:
        """Inicia o estágio LV2 (Game OS) do bootloader PS3"""
        try:
            self._log("[BOOTLOADER] Iniciando LV2 - Game OS...")
            
            # Simula inicialização do Game OS
            self._log("[LV2] Game OS kernel loading...")
            self._log("[LV2] Device drivers initialization...")
            self._log("[LV2] User services startup...")
            self._log("[LV2] XMB preparation...")
            
            # Procura módulos necessários para LV2
            cpu_loaded = any(name.startswith('gscx_cpu_cell') for name, _ in self.loaded)
            gpu_loaded = any(name.startswith('gscx_gpu_rsx') for name, _ in self.loaded)
            
            if cpu_loaded and gpu_loaded:
                self._log("[LV2] All required modules loaded")
                self._log("[LV2] System ready for game execution")
                return True
            else:
                self._log("[LV2] Missing required modules (CPU/GPU)")
                return False
                
        except Exception as e:
            self._log(f"[LV2] Error during Game OS initialization: {e}")
            return False
    
    def initialize_syscon(self) -> bool:
        """Inicializa o SYSCON (System Controller) virtual"""
        try:
            self._log("[SYSCON] Initializing System Controller...")
            
            # Procura módulo SYSCON carregado
            for name, lib in self.loaded:
                if name.startswith('gscx_syscon'):
                    try:
                        syscon_init = getattr(lib, 'GSCX_SYSCON_Initialize')
                        syscon_init.restype = c_bool
                        syscon_init.argtypes = []
                        
                        result = syscon_init()
                        if result:
                            self._log("[SYSCON] Power management initialized")
                            self._log("[SYSCON] Temperature monitoring active")
                            self._log("[SYSCON] Fan control enabled")
                            self._log("[SYSCON] System controller ready")
                            return True
                        else:
                            self._log("[SYSCON] Initialization failed")
                            return False
                    except AttributeError:
                        self._log("[SYSCON] Entry point not found")
                        return False
            
            # Fallback: simulação básica do SYSCON
            self._log("[SYSCON] Using virtual SYSCON simulation")
            self._log("[SYSCON] Virtual power management active")
            self._log("[SYSCON] Virtual temperature monitoring active")
            return True
            
        except Exception as e:
            self._log(f"[SYSCON] Error during initialization: {e}")
            return False
    
    def perform_hardware_detection(self) -> dict:
        """Realiza detecção de hardware do sistema PS3"""
        try:
            self._log("[HW] Starting hardware detection...")
            
            # Simulação de detecção de hardware baseada na documentação
            hardware_info = {
                'cpu': {
                    'type': 'Cell Broadband Engine',
                    'ppu_cores': 1,
                    'spu_cores': 8,
                    'frequency': '3.2 GHz'
                },
                'memory': {
                    'xdr_ram': '256 MB',
                    'gddr3_vram': '256 MB',
                    'total': '512 MB'
                },
                'gpu': {
                    'type': 'RSX Reality Synthesizer',
                    'frequency': '500 MHz',
                    'memory_interface': '128-bit GDDR3'
                },
                'storage': {
                    'hdd_interface': 'SATA',
                    'optical_drive': 'Blu-ray/DVD/CD',
                    'flash_memory': 'NAND/NOR'
                },
                'connectivity': {
                    'ethernet': '10/100/1000 Mbps',
                    'wifi': '802.11b/g (optional)',
                    'bluetooth': '2.0 + EDR',
                    'usb': '4x USB 2.0'
                }
            }
            
            # Log da detecção
            self._log(f"[HW] CPU: {hardware_info['cpu']['type']}")
            self._log(f"[HW] Memory: {hardware_info['memory']['total']} total")
            self._log(f"[HW] GPU: {hardware_info['gpu']['type']}")
            self._log(f"[HW] Storage: {hardware_info['storage']['optical_drive']}")
            self._log("[HW] Hardware detection completed")
            
            return hardware_info
            
        except Exception as e:
            self._log(f"[HW] Error during hardware detection: {e}")
            return {}
    
    def validate_boot_chain(self) -> bool:
        """Valida a integridade da cadeia de boot, seleciona ROS e verifica LV0/Appldr com fallback"""
        try:
            self._log("[SEC] Starting boot chain validation...")

            # Simulação de validação de segurança base
            validation_steps = [
                ("Boot ROM signature", True),
                ("LV0 integrity check", True),
                ("LV1 signature verification", True),
                ("LV2 authenticity check", True),
                ("Hardware authenticity", True),
                ("Anti-tampering detection", True)
            ]

            all_valid = True
            for step_name, is_valid in validation_steps:
                if is_valid:
                    self._log(f"[SEC] {step_name}: PASSED")
                else:
                    self._log(f"[SEC] {step_name}: FAILED")
                    all_valid = False

            # Seleção de ROS com verificação de LV0/Appldr
            selected = self.select_ros_slot()
            if selected:
                self._log(f"[SEC] ROS slot selected: {selected.upper()}")
                if not self._verify_lv0_and_appldr():
                    self._log("[SEC] LV0/Appldr verification failed for selected ROS")
                    # Fallback para outro slot
                    other = 'ros1' if selected == 'ros0' else 'ros0'
                    alt = self.select_ros_slot(preferred=other)
                    if alt and self._verify_lv0_and_appldr():
                        self._log(f"[SEC] Fallback to {alt.upper()} succeeded")
                    else:
                        self._log("[SEC] Fallback ROS verification failed")
                        all_valid = False
                else:
                    self._log("[SEC] LV0/Appldr verification: PASSED")
            else:
                self._log("[SEC] No valid ROS slot available")
                all_valid = False

            if all_valid:
                self._log("[SEC] Boot chain validation completed successfully")
                self._log("[SEC] System integrity verified")
            else:
                self._log("[SEC] Boot chain validation failed")

            return all_valid

        except Exception as e:
            self._log(f"[SEC] Error during boot chain validation: {e}")
            return False
    
    def execute_full_boot_sequence(self) -> bool:
        """Executa a sequência completa de boot do PS3 (LV0 -> LV1 -> LV2)"""
        try:
            self._log("[BOOT] Starting complete PS3 boot sequence...")
            
            # 1. Detecção de hardware
            hardware_info = self.perform_hardware_detection()
            if not hardware_info:
                self._log("[BOOT] Hardware detection failed")
                return False
            
            # 2. Inicialização do SYSCON
            if not self.initialize_syscon():
                self._log("[BOOT] SYSCON initialization failed")
                return False
            
            # 3. Validação da cadeia de boot
            if not self.validate_boot_chain():
                self._log("[BOOT] Boot chain validation failed")
                return False

            # 3.5 Inicialização do Flash Virtual (NAND/NOR)
            try:
                self._log("[BOOT] Initializing virtual flash (NAND/NOR emulation)...")
                vinfo = self.initialize_virtual_flash()
                if not self.mount_virtual_flash():
                    self._log("[BOOT] Virtual flash mount failed")
                    return False
                self._log(f"[BOOT] Virtual flash ready at {vinfo.get('path', '?')}")
            except Exception as e:
                self._log(f"[BOOT] Virtual flash initialization error: {e}")
                return False
            
            # 4. Execução dos estágios LV0, LV1, LV2
            if not self.boot_lv0_stage():
                self._log("[BOOT] LV0 stage failed")
                return False
            
            if not self.boot_lv1_stage():
                self._log("[BOOT] LV1 stage failed")
                return False
            
            if not self.boot_lv2_stage():
                self._log("[BOOT] LV2 stage failed")
                return False
            
            self._log("[BOOT] Complete boot sequence finished successfully")
            self._log("[BOOT] PS3 system ready for operation")
            return True
            
        except Exception as e:
            self._log(f"[BOOT] Error during complete boot sequence: {e}")
            return False

    def allocate_virtual_hdd(self, file_path: str, size_gb: int) -> str:
        """
        Cria/realoca um HDD virtual com tamanho informado.
        - file_path: caminho completo do arquivo .img/.vhd a ser criado
        - size_gb: tamanho em gigabytes (inteiro)
        Retorna o caminho final do arquivo criado.
        """
        size_gb = max(1, int(size_gb))
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        bytes_total = size_gb * 1024 * 1024 * 1024
        try:
            with open(file_path, 'wb') as f:
                f.seek(bytes_total - 1)
                f.write(b"\0")
            self.last_hdd_path = os.path.abspath(file_path)
            if self.on_log:
                self.on_log(f"[Storage] HDD virtual alocado: {self.last_hdd_path} ({size_gb} GB)")
            return self.last_hdd_path
        except Exception as e:
            if self.on_log:
                self.on_log(f"[Storage] Erro ao alocar HDD virtual: {e}")
            raise

    # --- Virtual Flash (NAND/NOR) emulado ---
    def initialize_virtual_flash(self) -> dict:
        """
        Inicializa uma estrutura de Flash virtual (NAND/NOR) com partições e arquivos
        placeholder para simular o Bootloader/Recovery e o layout do PS3.
        Retorna um dicionário com informações (path, partitions, ros_slots).
        """
        try:
            base_dir = getattr(self, "_vflash_dir", None)
            if not base_dir:
                if not self._temp_dir:
                    self._temp_dir = tempfile.mkdtemp(prefix='gscx_runtime_')
                base_dir = os.path.join(self._temp_dir, "vflash")
                self._vflash_dir = base_dir
            os.makedirs(base_dir, exist_ok=True)

            partitions = ["dev_flash", "dev_flash2", "dev_flash3"]
            ros_slots = ["ros0", "ros1"]
            for p in partitions + ros_slots + ["bootloader", "registry"]:
                os.makedirs(os.path.join(base_dir, p), exist_ok=True)

            # Arquivos placeholder
            try:
                with open(os.path.join(base_dir, "bootloader", "version.txt"), "w", encoding="utf-8") as f:
                    f.write("GSCX PS3 Bootloader (virtual)\n")
                for slot in ros_slots:
                    # LV0 e Appldr placeholders para cada ROS
                    with open(os.path.join(base_dir, slot, "lv0.self"), "w", encoding="utf-8") as f:
                        f.write("stub")
                    with open(os.path.join(base_dir, slot, "appldr.self"), "w", encoding="utf-8") as f:
                        f.write("stub")
                with open(os.path.join(base_dir, "registry", "xRegistry.sys"), "wb") as f:
                    f.write(b"\x00" * 1024)
            except Exception:
                pass

            info = {
                "path": os.path.abspath(base_dir),
                "partitions": partitions,
                "ros_slots": [s.upper() for s in ros_slots],
            }
            self._vflash_info = info
            self._log(f"[VFLASH] Virtual flash initialized at {info['path']}")
            return info
        except Exception as e:
            self._log(f"[VFLASH] Error initializing virtual flash: {e}")
            raise

    def mount_virtual_flash(self) -> bool:
        """Simula montagem das partições do flash virtual."""
        try:
            info = getattr(self, "_vflash_info", None)
            if not info:
                info = self.initialize_virtual_flash()
            self._log("[VFLASH] Partitions mounted: " + ", ".join(info["partitions"]))
            return True
        except Exception as e:
            self._log(f"[VFLASH] Failed to mount virtual flash: {e}")
            return False

    # --- Utilitários de Boot/ROS ---
    def select_ros_slot(self, preferred: Optional[str] = None) -> Optional[str]:
        """Seleciona um slot ROS válido (ros0/ros1) com opção de preferência e fallback."""
        try:
            base = self.get_vflash_info().get("path")
            candidates = ['ros0', 'ros1']
            if preferred in candidates:
                candidates = [preferred] + [c for c in candidates if c != preferred]

            def _valid(slot: str) -> bool:
                lv0_path = os.path.join(base, slot, 'lv0.self')
                return os.path.exists(lv0_path) and os.path.getsize(lv0_path) > 0

            for slot in candidates:
                if _valid(slot):
                    self._active_ros = slot
                    self._log(f"[ROS] Selected slot: {slot.upper()}")
                    return slot
            self._active_ros = None
            return None
        except Exception as e:
            self._log(f"[ROS] Error selecting slot: {e}")
            self._active_ros = None
            return None

    def _verify_lv0_and_appldr(self) -> bool:
        """Verifica a existência/integridade básica de LV0 e Appldr no ROS ativo."""
        try:
            base = self.get_vflash_info().get("path")
            slot = getattr(self, "_active_ros", None)
            if not slot:
                return False
            lv0_path = os.path.join(base, slot, 'lv0.self')
            appldr_path = os.path.join(base, slot, 'appldr.self')
            ok = True
            if not (os.path.exists(lv0_path) and os.path.getsize(lv0_path) > 0):
                self._log("[SEC] LV0 missing or invalid")
                ok = False
            if not (os.path.exists(appldr_path) and os.path.getsize(appldr_path) > 0):
                self._log("[SEC] Appldr missing or invalid")
                ok = False
            return ok
        except Exception as e:
            self._log(f"[SEC] Error verifying LV0/Appldr: {e}")
            return False

    # --- Operações de manutenção do VFlash ---
    def format_virtual_flash(self) -> dict:
        """Formata (recria) a estrutura do flash virtual preservando a pasta-base."""
        info = self.get_vflash_info()
        base = info.get('path')
        try:
            # Limpar conteúdo atual
            for name in os.listdir(base):
                full = os.path.join(base, name)
                try:
                    if os.path.isdir(full):
                        shutil.rmtree(full, ignore_errors=True)
                    else:
                        os.remove(full)
                except Exception:
                    pass
            # Resetar info e recriar
            self._vflash_info = None
            new_info = self.initialize_virtual_flash()
            self.mount_virtual_flash()
            self._log("[VFLASH] Virtual flash formatted")
            return new_info
        except Exception as e:
            self._log(f"[VFLASH] Error formatting virtual flash: {e}")
            raise

    def clean_vflash_partition(self, partition: str) -> bool:
        """Limpa arquivos de uma partição especificada (ex.: dev_flash2)."""
        base = self.get_vflash_info().get('path')
        target = os.path.join(base, partition)
        if not os.path.isdir(target):
            self._log(f"[VFLASH] Partition not found: {partition}")
            return False
        try:
            for name in os.listdir(target):
                full = os.path.join(target, name)
                try:
                    if os.path.isdir(full):
                        shutil.rmtree(full, ignore_errors=True)
                    else:
                        os.remove(full)
                except Exception:
                    pass
            self._log(f"[VFLASH] Partition cleaned: {partition}")
            return True
        except Exception as e:
            self._log(f"[VFLASH] Error cleaning partition {partition}: {e}")
            return False

    def clean_all_vflash_partitions(self) -> bool:
        """Limpa todas as partições listadas em get_vflash_info()."""
        info = self.get_vflash_info()
        ok = True
        for p in info.get('partitions', []):
            ok = self.clean_vflash_partition(p) and ok
        return ok

    def get_vflash_info(self) -> dict:
        """Retorna informações do flash virtual, inicializando se necessário."""
        info = getattr(self, "_vflash_info", None)
        if not info:
            info = self.initialize_virtual_flash()
        return info

# --- Lua Scripting (optional via 'lupa') ---
try:
    import time as _time
    import types as _types
    from typing import Any as _Any, Callable as _Callable
    try:
        import lupa as _lupa
        from lupa import LuaRuntime as _LuaRuntime
    except Exception:  # noqa: E722
        _lupa = None
        _LuaRuntime = None
except Exception:  # noqa: E722
    _lupa = None
    _LuaRuntime = None
    _time = None
    _types = None
    _Any = None
    _Callable = None

class ScriptingEngine:
    """Simple Lua scripting engine powered by 'lupa' (LuaJIT) when available.
    Provides a minimal API table 'gscx' to interact with the emulator loader.
    """
    def __init__(self, loader: ModulesLoader, on_output: _Callable[[str], None] | None = None):
        self.loader = loader
        self.on_output = on_output
        self._lua = None
        self._cancel = False
        if _LuaRuntime is not None:
            try:
                self._lua = _LuaRuntime(unpack_returned_tuples=True)
            except Exception:
                self._lua = None

    def available(self) -> bool:
        return self._lua is not None

    def _emit(self, text: str):
        try:
            if self.on_output:
                self.on_output(text)
        except Exception:
            pass
        try:
            # also bridge to native/console log handler
            _LogBridge.handle(text.encode('utf-8', errors='ignore'))
        except Exception:
            pass

    def cancel(self):
        """Requests cooperative cancel. Scripts should check gscx.check_cancel()."""
        self._cancel = True

    def _api_table(self):
        def _print(*args):
            msg = " ".join(str(a) for a in args)
            self._emit(msg + "\n")
        def _log(msg=""):
            self._emit(str(msg) + "\n")
        def _sleep(ms: int = 0):
            if _time is None:
                return
            # sleep in small chunks to allow cooperative cancel
            total = max(0, int(ms)) / 1000.0
            step = 0.05
            elapsed = 0.0
            while elapsed < total and not self._cancel:
                _time.sleep(min(step, total - elapsed))
                elapsed += step
        def _check_cancel():
            return bool(self._cancel)
        # Bindings to ModulesLoader
        def _load_default_modules():
            self.loader.load_default_modules()
        def _load_bundle(path: str):
            self.loader.load_from_gscore(path)
        def _boot_recovery(pup_path: str | None = None, usb_dir: str | None = None):
            self.loader.boot_recovery(pup_path, usb_dir)
        def _setenv(name: str, value: str):
            os.environ[str(name)] = str(value)
        def _getenv(name: str, default: str | None = None):
            return os.environ.get(str(name), default)
        # Filesystem helpers
        def _cwd():
            return os.getcwd()
        def _chdir(path: str):
            os.chdir(str(path))
        def _exists(path: str):
            return os.path.exists(str(path))
        def _join(*parts):
            return os.path.join(*(str(p) for p in parts))
        def _abspath(path: str):
            return os.path.abspath(str(path))
        def _dirname(path: str):
            return os.path.dirname(str(path))
        def _basename(path: str):
            return os.path.basename(str(path))
        def _listdir(path: str = "."):
            return os.listdir(str(path))
        def _read_text(path: str, encoding: str = 'utf-8'):
            with open(str(path), 'r', encoding=encoding) as f:
                return f.read()
        def _write_text(path: str, content, encoding: str = 'utf-8'):
            with open(str(path), 'w', encoding=encoding) as f:
                f.write(str(content))
            return True
        def _mkdir(path: str, exist_ok: bool = True):
            os.makedirs(str(path), exist_ok=bool(exist_ok))
            return True
        return {
            'print': _print,
            'log': _log,
            'sleep': _sleep,
            'check_cancel': _check_cancel,
            'load_modules': _load_default_modules,
            'load_bundle': _load_bundle,
            'boot_recovery': _boot_recovery,
            'setenv': _setenv,
            'getenv': _getenv,
            'cwd': _cwd,
            'chdir': _chdir,
            'exists': _exists,
            'join': _join,
            'abspath': _abspath,
            'dirname': _dirname,
            'basename': _basename,
            'listdir': _listdir,
            'read_text': _read_text,
            'write_text': _write_text,
            'mkdir': _mkdir,
        }

    def run(self, code: str, script_path: str | None = None, extra_globals: dict | None = None):
        """Execute Lua code. Raises RuntimeError if 'lupa' is not available."""
        if not self.available():
            raise RuntimeError("Lua runtime not available. Please install 'lupa' (pip install lupa).")
        self._cancel = False
        # Working directory to script's folder
        cwd_backup = os.getcwd()
        try:
            if script_path:
                sp = os.path.abspath(script_path)
                if os.path.isfile(sp):
                    os.chdir(os.path.dirname(sp))
            # Prepare environment
            G = self._lua.globals()
            # inject our API
            api = self._api_table()
            # override lua 'print'
            G['print'] = api['print']
            G['gscx'] = api
            if extra_globals:
                for k, v in extra_globals.items():
                    G[str(k)] = v
            # Execute
            self._lua.execute(code)
        finally:
            try:
                os.chdir(cwd_backup)
            except Exception:
                pass

    def run_file(self, file_path: str, extra_globals: dict | None = None):
        """Convenience to execute a Lua script from a filesystem path."""
        file_path = os.path.abspath(file_path)
        if not os.path.isfile(file_path):
            raise FileNotFoundError(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        return self.run(code, script_path=file_path, extra_globals=extra_globals)