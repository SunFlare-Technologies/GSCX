import sys
import os
import json
import re
from datetime import datetime
from typing import Optional, Dict, Any
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QToolBar, QLabel, QComboBox, QPushButton, QGroupBox, QRadioButton,
    QCheckBox, QLineEdit, QFileDialog, QMessageBox, QProgressBar,
    QStackedWidget, QFrame, QScrollArea, QGridLayout, QSpacerItem,
    QSizePolicy, QTextEdit, QDoubleSpinBox, QSpinBox, QProgressDialog,
    QSplashScreen, QSplitter, QPlainTextEdit, QToolButton, QMenu, QDialog, QListWidget
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QSize, QRegularExpression, QUrl
from PySide6.QtGui import QAction, QIcon, QPixmap, QPainter, QFont, QSyntaxHighlighter, QTextCharFormat, QColor, QDesktopServices
from .modules_loader import ModulesLoader, ScriptingEngine
from .i18n import t, set_language, get_language, LANG_DISPLAY


class PS3ModelValidator(QThread):
    """Thread para validar modelos de PS3 via API"""
    validation_complete = Signal(bool, str)  # success, model_info
    
    def __init__(self, model_name: str):
        super().__init__()
        self.model_name = model_name
    
    def run(self):
        try:
            # Carrega e valida a partir do ps3_models.json
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            json_path = os.path.join(project_root, 'ps3_models.json')
            if not os.path.exists(json_path):
                # Fallback heurístico quando o arquivo não existe
                model_upper = self.model_name.upper().strip()
                mcode = model_upper.replace('-', '')
                console_type = "fat"
                if mcode.startswith("CECH"):
                    suffix = mcode[4:]
                    if suffix and suffix[0].isalpha():
                        console_type = "fat"
                    else:
                        digits = re.findall(r'\d+', mcode)
                        if digits:
                            try:
                                d = int(digits[0][:2])
                            except Exception:
                                d = 0
                            if d >= 40:
                                console_type = "super_slim"
                            elif d >= 20:
                                console_type = "slim"
                            else:
                                console_type = "fat"
                response = {
                    "type": console_type,
                    "description": f"{model_upper} • {console_type.replace('_',' ').title()} • (dados padrão)",
                    "year": None,
                    "storage": None,
                    "media": [],
                    "retrocompatibility": False,
                    "model": model_upper,
                }
                self.validation_complete.emit(True, json.dumps(response, ensure_ascii=False))
                return

            with open(json_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError as je:
                    data = None

            model_upper = self.model_name.upper().strip()
            candidates = {model_upper, model_upper.replace('-', '')}

            found_category = None
            found_model_key = None
            found_info = None

            # Fallback: se o banco estiver inválido, inferir tipo do console de forma heurística
            if not isinstance(data, dict):
                mcode = model_upper.replace('-', '')
                console_type = "fat"
                if mcode.startswith("CECH"):
                    suffix = mcode[4:]
                    if suffix and suffix[0].isalpha():
                        console_type = "fat"
                    else:
                        digits = re.findall(r'\d+', mcode)
                        if digits:
                            try:
                                d = int(digits[0][:2])
                            except Exception:
                                d = 0
                            if d >= 40:
                                console_type = "super_slim"
                            elif d >= 20:
                                console_type = "slim"
                            else:
                                console_type = "fat"
                response = {
                    "type": console_type,
                    "description": f"{model_upper} • {console_type.replace('_',' ').title()} • (dados padrão)",
                    "year": None,
                    "storage": None,
                    "media": [],
                    "retrocompatibility": False,
                    "model": model_upper,
                }
                self.validation_complete.emit(True, json.dumps(response, ensure_ascii=False))
                return

            for category, models in data.items():
                for key, info in models.items():
                    key_upper = key.upper()
                    key_variants = {key_upper, key_upper.replace('-', '')}
                    if candidates & key_variants:
                        found_category = category
                        found_model_key = key
                        found_info = info
                        break
                if found_info:
                    break

            if found_info:
                response = {
                    "type": found_category,
                    "description": f"{found_model_key} • {found_category.replace('_',' ').title()} • {found_info.get('storage','')} • {found_info.get('year','')}",
                    "year": found_info.get('year'),
                    "storage": found_info.get('storage'),
                    "media": found_info.get('media', []),
                    "retrocompatibility": found_info.get('retrocompatibility', False),
                    "model": found_model_key,
                }
                self.validation_complete.emit(True, json.dumps(response, ensure_ascii=False))
            else:
                self.validation_complete.emit(False, "Modelo não encontrado")
                
        except Exception as e:
            self.validation_complete.emit(False, f"Erro na validação: {str(e)}")


class PS3ConsoleWidget(QWidget):
    """Widget para mostrar representação visual do console PS3"""
    
    def __init__(self):
        super().__init__()
        self.console_type = "fat"  # fat, slim, super_slim
        self.setMinimumSize(300, 200)
        self.setStyleSheet("""
            PS3ConsoleWidget {
                background-color: #2b2b2b;
                border: 2px solid #555;
                border-radius: 10px;
            }
        """)
    
    def set_console_type(self, console_type: str):
        self.console_type = console_type
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Desenha representação do console baseado no tipo
        rect = self.rect().adjusted(10, 10, -10, -10)
        
        if self.console_type == "fat":
            painter.fillRect(rect, Qt.black)
            painter.setPen(Qt.white)
            painter.drawText(rect, Qt.AlignCenter, "PS3 FAT\n(Original)")
        elif self.console_type == "slim":
            painter.fillRect(rect, Qt.darkGray)
            painter.setPen(Qt.white)
            painter.drawText(rect, Qt.AlignCenter, "PS3 SLIM\n(Redesign)")
        elif self.console_type == "super_slim":
            painter.fillRect(rect, Qt.gray)
            painter.setPen(Qt.black)
            painter.drawText(rect, Qt.AlignCenter, "PS3 SUPER SLIM\n(Final)")


class RecoveryBootThread(QThread):
    success = Signal()
    error = Signal(str)

    def __init__(self, modules_loader: ModulesLoader, pup: Optional[str], usb_dir: Optional[str]):
        super().__init__()
        self.modules_loader = modules_loader
        self.pup = pup
        self.usb_dir = usb_dir

    def run(self):
        try:
            self.modules_loader.load_default_modules()
            self.modules_loader.boot_recovery(self.pup, usb_dir=self.usb_dir)
            self.success.emit()
        except Exception as e:
            self.error.emit(str(e))


class PS3SetupWidget(QWidget):
    """Widget principal para setup do PS3"""
    
    recovery_started = Signal()
    
    def __init__(self, modules_loader: ModulesLoader):
        super().__init__()
        self.modules_loader = modules_loader
        self.validator_thread = None
        self.recovery_thread = None
        self.progress_dialog = None
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Título
        title = QLabel("Configuração do Console PS3")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Layout principal (sem toolbars laterais)
        main_layout = QHBoxLayout()
        
        # Área central
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        
        # Seção de modelo do console - CENTRALIZADA NO TOPO
        model_group = QGroupBox("Modelo do Console")
        model_group.setMaximumHeight(350)  # Aumentado para acomodar a imagem
        model_layout = QVBoxLayout(model_group)
        
        # Imagem do console acima do seletor
        self.console_image_label = QLabel()
        self.console_image_label.setAlignment(Qt.AlignCenter)
        self.console_image_label.setMinimumHeight(120)
        self.console_image_label.setMaximumHeight(120)
        self.console_image_label.setStyleSheet("""
            QLabel {
                border: 2px solid #ccc;
                border-radius: 8px;
                background-color: #f9f9f9;
                padding: 10px;
            }
        """)
        # Carrega imagem padrão (PS3 Fat)
        self.update_console_image("fat")
        model_layout.addWidget(self.console_image_label)
        
        # Input do modelo centralizado
        model_input_layout = QHBoxLayout()
        model_input_layout.addStretch()
        model_input_layout.addWidget(QLabel("Modelo:"))
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("Ex: CECHA01, CECH-2001A, CECH-4001B")
        self.model_input.setMaximumWidth(300)
        model_input_layout.addWidget(self.model_input)
        
        self.validate_btn = QPushButton("Validar")
        self.validate_btn.clicked.connect(self.validate_model)
        model_input_layout.addWidget(self.validate_btn)
        model_input_layout.addStretch()
        
        model_layout.addLayout(model_input_layout)
        
        # Ações rápidas abaixo do seletor: Disco e Power
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(16)
        actions_layout.setAlignment(Qt.AlignCenter)

        # Handlers internos para alternância
        self._virt_win = None
        def _on_power_toggled(checked: bool):
            try:
                if checked:
                    self.power_btn.setText("Power\nOff")
                    # Inicia sequência de boot do PS3
                    self.start_ps3_boot_sequence()
                else:
                    self.power_btn.setText("Power\nOn")
                    self.shutdown_ps3_system()
            except Exception:
                self.power_btn.blockSignals(True)
                self.power_btn.setChecked(False)
                self.power_btn.setText("Power\nOn")
                self.power_btn.blockSignals(False)

        def _on_disc_toggled(inserted: bool):
            try:
                if inserted:
                    self.disc_btn.setText("Ejetar\nDisco")
                    QMessageBox.information(self, "Disco Virtual", "Disco inserido (virtual)")
                else:
                    self.disc_btn.setText("Injetar\nDisco")
                    QMessageBox.information(self, "Disco Virtual", "Disco ejetado (virtual)")
            except Exception:
                pass

        self.disc_btn = QToolButton()
        self.disc_btn.setText("Injetar\nDisco")
        self.disc_btn.setCheckable(True)
        self.disc_btn.setEnabled(False)
        self.disc_btn.setFixedSize(80, 80)
        actions_layout.addWidget(self.disc_btn)
        self.disc_btn.toggled.connect(_on_disc_toggled)

        self.power_btn = QToolButton()
        self.power_btn.setText("Power\nOn")
        self.power_btn.setCheckable(True)
        self.power_btn.setEnabled(False)
        self.power_btn.setFixedSize(80, 80)
        actions_layout.addWidget(self.power_btn)
        self.power_btn.toggled.connect(_on_power_toggled)

        model_layout.addLayout(actions_layout)

        # Widget visual do console
        self.console_widget = PS3ConsoleWidget()
        self.console_widget.setMinimumHeight(140)
        model_layout.addWidget(self.console_widget)
        
        # Status da validação centralizado
        self.validation_status = QLabel("Digite um modelo para validar")
        self.validation_status.setStyleSheet("color: gray;")
        self.validation_status.setAlignment(Qt.AlignCenter)
        model_layout.addWidget(self.validation_status)
        
        central_layout.addWidget(model_group)
        
        # Layout 3x1 para controles principais
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(20)
        
        # 1. Atribuidor de Disco
        disc_group = self.create_disc_control_group()
        controls_layout.addWidget(disc_group)
        
        # 2. Controles
        control_group = self.create_controller_group()
        controls_layout.addWidget(control_group)
        
        # 3. Configurações (substitui GPU)
        config_group = self.create_config_group()
        controls_layout.addWidget(config_group)
        
        central_layout.addLayout(controls_layout)
        
        # Configurações avançadas removidas da UI neste modo simplificado.
        # Mantemos apenas: Modelo do Console, Atribuidor de Disco, Controles e Configurações.
        # As opções avançadas continuam acessíveis por futuras telas e o menu.

        
        main_layout.addWidget(central_widget)
        
        layout.addLayout(main_layout)
        
        # Carregar configuração do usuário, se existir
        try:
            self.load_configuration()
        except Exception:
            pass
    
    def update_console_image(self, console_type: str):
        """Atualiza a imagem do console baseada no tipo"""
        try:
            # Mapeia tipos de console para arquivos de imagem
            image_map = {
                "fat": "PS3-fat.png",
                "slim": "PS3-slim.png", 
                "super_slim": "PS3-spslim.png"
            }
            
            # Determina o arquivo de imagem
            image_file = image_map.get(console_type, "PS3-fat.png")
            
            # Caminho para a imagem
            ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            image_path = os.path.join(ROOT_DIR, 'docs', 'assets', image_file)
            
            if os.path.exists(image_path):
                # Carrega e redimensiona a imagem
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # Redimensiona mantendo proporção
                    scaled_pixmap = pixmap.scaled(200, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.console_image_label.setPixmap(scaled_pixmap)
                else:
                    self.console_image_label.setText(f"Console {console_type.upper()}")
            else:
                # Fallback para texto se imagem não existir
                self.console_image_label.setText(f"Console {console_type.upper()}")
                
        except Exception as e:
             # Fallback em caso de erro
             self.console_image_label.setText(f"Console {console_type.upper()}")
    
    def start_ps3_boot_sequence(self):
        """Inicia sequência completa de boot do PS3"""
        try:
            # Cria janela de boot do PS3
            self._boot_dialog = QDialog(self)
            self._boot_dialog.setWindowTitle("PlayStation 3 System Boot")
            self._boot_dialog.setMinimumSize(600, 450)
            self._boot_dialog.setModal(True)
            
            layout = QVBoxLayout(self._boot_dialog)
            
            # Header do sistema
            header = QLabel("PlayStation®3 System")
            header.setFont(QFont("Arial", 16, QFont.Bold))
            header.setAlignment(Qt.AlignCenter)
            header.setStyleSheet("color: white; background-color: #1e1e1e; padding: 10px; border-radius: 5px;")
            layout.addWidget(header)
            
            # Console de boot
            self._boot_console = QTextEdit()
            self._boot_console.setStyleSheet("""
                QTextEdit {
                    background-color: black;
                    color: #00ff00;
                    font-family: 'Courier New', monospace;
                    font-size: 11px;
                    border: 2px solid #333;
                }
            """)
            self._boot_console.setReadOnly(True)
            layout.addWidget(self._boot_console)
            
            # Barra de progresso
            self._boot_progress = QProgressBar()
            self._boot_progress.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #333;
                    border-radius: 5px;
                    text-align: center;
                    background-color: #2b2b2b;
                    color: white;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 3px;
                }
            """)
            layout.addWidget(self._boot_progress)
            
            # Status label
            self._boot_status = QLabel("Initializing...")
            self._boot_status.setAlignment(Qt.AlignCenter)
            self._boot_status.setStyleSheet("color: white; font-weight: bold; padding: 5px;")
            layout.addWidget(self._boot_status)
            
            self._boot_dialog.show()
            
            # Inicia sequência de boot
            self._boot_step = 0
            self._boot_timer = QTimer()
            self._boot_timer.timeout.connect(self._execute_boot_step)
            self._boot_timer.start(800)  # 800ms entre cada step
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao iniciar sistema PS3: {e}")
    
    def _execute_boot_step(self):
        """Executa cada passo da sequência de boot"""
        boot_steps = [
            (5, "System Check", "[SYSCON] Initializing System Controller..."),
            (10, "Hardware Init", "[HW] Cell Broadband Engine detected\n[HW] PPU Core initialized\n[HW] SPU Cores (1-8) initialized"),
            (20, "Memory Test", "[MEM] XDR RAM: 256MB detected\n[MEM] GDDR3 VRAM: 256MB detected\n[MEM] Memory test passed"),
            (30, "RSX Init", "[RSX] Graphics Synthesizer initializing...\n[RSX] VRAM allocation complete"),
            (40, "Hypervisor", "[HV] PlayStation 3 Hypervisor loading...\n[HV] LPAR initialization complete"),
            (50, "Security", "[SEC] Bootloader verification...\n[SEC] System integrity check passed"),
            (60, "I/O Systems", "[IO] USB Controllers initialized\n[IO] Bluetooth stack loaded\n[IO] Network interface ready"),
            (70, "File System", "[FS] Virtual File System mounted\n[FS] Game OS partition ready"),
            (80, "Audio/Video", "[AV] Audio processing unit ready\n[AV] Video output configured"),
            (90, "System Services", "[SYS] Background services starting...\n[SYS] Network services initialized"),
            (95, "Final Check", "[BOOT] All systems operational\n[BOOT] Ready for game execution"),
            (100, "Complete", "[SYSTEM] PlayStation 3 boot sequence complete!")
        ]
        
        if self._boot_step < len(boot_steps):
            progress, status, message = boot_steps[self._boot_step]
            
            self._boot_progress.setValue(progress)
            self._boot_status.setText(status)
            self._boot_console.append(message)
            
            # Scroll para o final
            cursor = self._boot_console.textCursor()
            cursor.movePosition(cursor.End)
            self._boot_console.setTextCursor(cursor)
            
            self._boot_step += 1
            
            # Se completou o boot
            if self._boot_step >= len(boot_steps):
                self._boot_timer.stop()
                # Executa sequência completa de boot do PS3
                try:
                     boot_success = self.modules_loader.execute_full_boot_sequence()
                     if not boot_success:
                         self._boot_console.append("[ERROR] Boot sequence failed - using fallback mode")
                         # Fallback: carrega módulos básicos
                         self.modules_loader.load_default_modules()
                except Exception as e:
                     self._boot_console.append(f"[ERROR] Boot sequence error: {e}")
                     # Fallback: carrega módulos básicos
                     try:
                         self.modules_loader.load_default_modules()
                     except Exception:
                         pass
                
                # Fecha diálogo após 2 segundos
                QTimer.singleShot(2000, self._finish_boot_sequence)
    
    def _finish_boot_sequence(self):
        """Finaliza a sequência de boot e abre a interface principal"""
        try:
            if hasattr(self, '_boot_dialog'):
                self._boot_dialog.close()
            
            # Abre janela de virtualização
            self._virt_win = QDialog(self)
            self._virt_win.setWindowTitle("PS3 System - Running")
            self._virt_win.setMinimumSize(520, 360)
            vlay = QVBoxLayout(self._virt_win)
            
            # Status do sistema
            status_label = QLabel(self.validation_status.text())
            status_label.setAlignment(Qt.AlignCenter)
            status_label.setStyleSheet("font-weight: bold; color: green;")
            vlay.addWidget(status_label)
            
            # Preview do console
            preview = PS3ConsoleWidget()
            try:
                preview.set_console_type(self.console_widget.console_type)
            except Exception:
                pass
            preview.setMinimumHeight(220)
            vlay.addWidget(preview)
            
            # Informações do sistema
            system_info = QLabel("Sistema PS3 virtualizado ativo\nTodos os módulos carregados com sucesso")
            system_info.setAlignment(Qt.AlignCenter)
            system_info.setStyleSheet("color: gray; font-size: 11px;")
            vlay.addWidget(system_info)

            # Informações do Flash Virtual (VFlash)
            try:
                vinfo = self.modules_loader.get_vflash_info()
                vflash_text = (
                    f"VFlash: {vinfo.get('path', '?')}\n"
                    f"Partições: {', '.join(vinfo.get('partitions', []))}\n"
                    f"ROS slots: {', '.join(vinfo.get('ros_slots', []))}"
                )
                vflash_label = QLabel(vflash_text)
                vflash_label.setAlignment(Qt.AlignCenter)
                vflash_label.setStyleSheet("color: #666; font-size: 10px;")
                vlay.addWidget(vflash_label)

                open_btn = QPushButton("Abrir pasta do VFlash")
                def _open_vflash():
                    try:
                        QDesktopServices.openUrl(QUrl.fromLocalFile(vinfo.get('path', '')))
                    except Exception:
                        pass
                open_btn.clicked.connect(_open_vflash)
                vlay.addWidget(open_btn, alignment=Qt.AlignCenter)
            except Exception:
                pass
            
            self._virt_win.show()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao finalizar boot: {e}")
    
    def shutdown_ps3_system(self):
        """Desliga o sistema PS3"""
        try:
            # Descarrega módulos
            try:
                self.modules_loader.unload_all()
            except Exception:
                pass
            
            # Fecha janelas abertas
            if hasattr(self, '_virt_win') and self._virt_win:
                self._virt_win.close()
                self._virt_win = None
            
            if hasattr(self, '_boot_dialog') and self._boot_dialog:
                self._boot_dialog.close()
            
            # Para timers se estiverem rodando
            if hasattr(self, '_boot_timer') and self._boot_timer:
                self._boot_timer.stop()
            
            QMessageBox.information(self, "Sistema", "Sistema PS3 desligado com sucesso")
            
        except Exception as e:
            QMessageBox.warning(self, "Aviso", f"Erro durante desligamento: {e}")
     
     # def create_left_toolbar(self):
    #     """Cria toolbar lateral esquerda (removida na UI simplificada)"""
    #     toolbar = QFrame()
    #     toolbar.setFrameStyle(QFrame.StyledPanel)
    #     toolbar.setMaximumWidth(150)
    #     toolbar.setStyleSheet("""
    #         QFrame {
    #             background-color: #f0f0f0;
    #             border: 1px solid #ccc;
    #             border-radius: 5px;
    #         }
    #     """)
    #     layout = QVBoxLayout(toolbar)
    #     layout.addWidget(QLabel("Informações"))
    #     info_buttons = [
    #         ("SYSCON", self.show_syscon_info),
    #         ("Memória", self.show_memory_info),
    #         ("I/O", self.show_io_info),
    #         ("CPU", self.show_cpu_info)
    #     ]
    #     for name, callback in info_buttons:
    #         btn = QPushButton(name)
    #         btn.clicked.connect(callback)
    #         btn.setMaximumHeight(30)
    #         layout.addWidget(btn)
    #     layout.addStretch()
    #     return toolbar
    
    def create_right_toolbar(self):
        """Cria toolbar lateral direita"""
        toolbar = QFrame()
        toolbar.setFrameStyle(QFrame.StyledPanel)
        toolbar.setMaximumWidth(150)
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)
        
        layout = QVBoxLayout(toolbar)
        layout.addWidget(QLabel("Ações"))
        
        # Botões de ação
        self.start_recovery_btn = QPushButton("Recovery\nMode")
        self.start_recovery_btn.clicked.connect(self.start_recovery_mode)
        self.start_recovery_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                font-size: 12px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        layout.addWidget(self.start_recovery_btn)
        
        self.save_config_btn = QPushButton("Salvar\nConfig")
        self.save_config_btn.clicked.connect(self.save_configuration)
        layout.addWidget(self.save_config_btn)
        
        layout.addStretch()
        return toolbar
    
    def create_disc_control_group(self):
        """Cria grupo de controle de disco"""
        disc_group = QGroupBox("Atribuidor de Disco")
        disc_group.setMaximumHeight(200)
        disc_layout = QVBoxLayout(disc_group)
        
        self.use_physical_drive = QCheckBox("Usar leitor físico")
        disc_layout.addWidget(self.use_physical_drive)
        
        drive_layout = QHBoxLayout()
        drive_layout.addWidget(QLabel("Drive:"))
        self.drive_combo = QComboBox()
        self.drive_combo.setEnabled(False)
        self.populate_drive_list()
        drive_layout.addWidget(self.drive_combo)
        disc_layout.addLayout(drive_layout)
        
        self.use_physical_drive.toggled.connect(self.drive_combo.setEnabled)
        
        # Botão para carregar ISO
        load_iso_btn = QPushButton("Carregar ISO")
        load_iso_btn.clicked.connect(self.load_iso_file)
        disc_layout.addWidget(load_iso_btn)
        
        return disc_group
    
    def create_controller_group(self):
        """Cria grupo de controles"""
        ctrl_group = QGroupBox("Controles")
        ctrl_group.setMaximumHeight(200)
        ctrl_layout = QVBoxLayout(ctrl_group)
        
        self.detect_input_btn = QPushButton("Detectar Input")
        self.detect_input_btn.clicked.connect(lambda: QMessageBox.information(self, "Controle", "Detecção de input: não implementado ainda"))
        ctrl_layout.addWidget(self.detect_input_btn)
        
        self.map_input_btn = QPushButton("Mapear Controle")
        self.map_input_btn.clicked.connect(lambda: QMessageBox.information(self, "Controle", "Mapeamento de controle: não implementado ainda"))
        ctrl_layout.addWidget(self.map_input_btn)
        
        # Status do controle
        self.controller_status = QLabel("Nenhum controle detectado")
        self.controller_status.setStyleSheet("color: gray; font-size: 10px;")
        ctrl_layout.addWidget(self.controller_status)
        
        return ctrl_group
    
    def create_config_group(self):
        """Cria grupo de configurações"""
        config_group = QGroupBox("Configurações")
        config_group.setMaximumHeight(200)
        config_layout = QVBoxLayout(config_group)
        
        # Botão para abrir configurações avançadas
        advanced_btn = QPushButton("Configurações\nAvançadas")
        advanced_btn.clicked.connect(self.open_advanced_settings)
        config_layout.addWidget(advanced_btn)
        
        # Botão para configurações de GPU
        gpu_btn = QPushButton("Configurar\nGPU")
        gpu_btn.clicked.connect(self.open_gpu_settings)
        config_layout.addWidget(gpu_btn)
        
        # Status das configurações
        self.config_status = QLabel("Configuração padrão")
        self.config_status.setStyleSheet("color: gray; font-size: 10px;")
        config_layout.addWidget(self.config_status)
        
        return config_group
    
    def load_iso_file(self):
        title = "Selecionar arquivo de mídia (ISO/PKG/RAP/ELF)"
        filters = (
            "Arquivos suportados (*.iso *.pkg *.rap *.elf);;"
            "Imagens ISO (*.iso);;"
            "Pacotes PKG (*.pkg);;"
            "Licenças RAP (*.rap);;"
            "Executáveis ELF (*.elf);;"
            "Todos os arquivos (*)"
        )
        file_path, _ = QFileDialog.getOpenFileName(self, title, "", filters)
        if file_path:
            try:
                self.on_log_message(f"Mídia selecionada: {file_path}")
                QMessageBox.information(self, "Mídia selecionada", os.path.basename(file_path))
            except Exception as e:
                QMessageBox.critical(self, t('general.error') if callable(t) else 'Erro', str(e))

    
    def open_advanced_settings(self):
        """Abre janela de configurações avançadas"""
        QMessageBox.information(self, "Configurações", "Configurações avançadas: em desenvolvimento")
    
    def open_gpu_settings(self):
        """Abre configurações de GPU"""
        QMessageBox.information(self, "GPU", "Configurações de GPU: em desenvolvimento")
    
    def show_syscon_info(self):
        QMessageBox.information(self, "SYSCON", "Sistema de controle do PS3\nStatus: Virtualizado")
    
    def show_memory_info(self):
        QMessageBox.information(self, "Memória", "Gerenciamento de memória do PS3\nRAM: 256MB XDR\nVRAM: 256MB GDDR3")
    
    def show_io_info(self):
        QMessageBox.information(self, "I/O", "Sistema de entrada/saída\nUSB, Bluetooth, Ethernet")
    
    def show_cpu_info(self):
        QMessageBox.information(self, "CPU", "Cell Broadband Engine\n1x PPE + 8x SPE")
    
    def allocate_hdd(self):
        path = (self.hdd_path.text() or '').strip()
        size_gb = int(self.hdd_size_gb.value())
        if not path:
            QMessageBox.warning(self, "HDD Virtual", "Informe o caminho do arquivo do HDD virtual (.img/.vhd)")
            return
        try:
            final_path = self.modules_loader.allocate_virtual_hdd(path, size_gb)
            QMessageBox.information(self, "HDD Virtual", f"HDD alocado com sucesso em:\n{final_path}")
        except Exception as e:
            QMessageBox.critical(self, "HDD Virtual", f"Falha ao alocar HDD: {e}")
    
    def save_configuration(self):
        try:
            root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            cfg_path = os.path.join(root, 'user_config.json')
            data = {
                'model': self.model_input.text().strip(),
                'gpu': {
                    'auto': (self.gpu_auto.isChecked() if hasattr(self, 'gpu_auto') else True),
                    'selected': (self.gpu_combo.currentText() if hasattr(self, 'gpu_combo') else ''),
                },
                'drive': {
                    'use_physical': self.use_physical_drive.isChecked(),
                    'selected': self.drive_combo.currentText(),
                },
                'firmware': {
                    'pup_path': (self.firmware_path.text().strip() if hasattr(self, 'firmware_path') else ''),
                    'usb_dir': (self.usb_dir_input.text().strip() if hasattr(self, 'usb_dir_input') else '')
                },
                'memory_gb': (float(self.mem_spin.value()) if hasattr(self, 'mem_spin') else 3.0),
                'hdd': {
                    'path': (self.hdd_path.text().strip() if hasattr(self, 'hdd_path') else ''),
                    'size_gb': (int(self.hdd_size_gb.value()) if hasattr(self, 'hdd_size_gb') else 0),
                },
                'graphics': {
                    'api': (self.gfx_api_combo.currentText() if hasattr(self, 'gfx_api_combo') else ''),
                    'render_mode': (self.render_combo.currentText() if hasattr(self, 'render_combo') else ''),
                    'filtering': (self.filter_combo.currentText() if hasattr(self, 'filter_combo') else ''),
                    'resolution': (self.res_combo.currentText() if hasattr(self, 'res_combo') else ''),
                    'osd': (self.osd_checkbox.isChecked() if hasattr(self, 'osd_checkbox') else False),
                },
                'processing': {
                    'clock_percent': (int(self.clock_spin.value()) if hasattr(self, 'clock_spin') else 100),
                    'ps2_ee': (self.ps2ee_checkbox.isChecked() if hasattr(self, 'ps2ee_checkbox') else False),
                },
            }
            with open(cfg_path, 'w', encoding='utf-8') as wf:
                json.dump(data, wf, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Configuração", f"Configuração salva em {cfg_path}")
        except Exception as e:
            QMessageBox.critical(self, "Configuração", f"Falha ao salvar configuração: {e}")
    
    def load_configuration(self):
        """Carrega user_config.json (se existir) e preenche os campos da UI."""
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        cfg_path = os.path.join(root, 'user_config.json')
        if not os.path.isfile(cfg_path):
            return
        try:
            with open(cfg_path, 'r', encoding='utf-8') as rf:
                cfg = json.load(rf)
        except Exception:
            return
        
        try:
            # Modelo
            self.model_input.setText((cfg.get('model') or '').strip())
            
            # GPU
            gpu = cfg.get('gpu') or {}
            auto = bool(gpu.get('auto', True))
            self.gpu_auto.setChecked(auto)
            self.gpu_manual.setChecked(not auto)
            sel_gpu = (gpu.get('selected') or '').strip()
            if sel_gpu:
                idx = self.gpu_combo.findText(sel_gpu)
                if idx >= 0:
                    self.gpu_combo.setCurrentIndex(idx)
                else:
                    self.gpu_combo.addItem(sel_gpu)
                    self.gpu_combo.setCurrentText(sel_gpu)
            
            # Drive
            drv = cfg.get('drive') or {}
            use_phys = bool(drv.get('use_physical', False))
            self.use_physical_drive.setChecked(use_phys)
            sel_drv = (drv.get('selected') or '').strip()
            if sel_drv:
                idx = self.drive_combo.findText(sel_drv)
                if idx >= 0:
                    self.drive_combo.setCurrentIndex(idx)
                else:
                    self.drive_combo.addItem(sel_drv)
                    self.drive_combo.setCurrentText(sel_drv)
            
            # Firmware
            fw = cfg.get('firmware') or {}
            pup = (fw.get('pup_path') or '').strip()
            if pup and hasattr(self, 'firmware_path'):
                self.firmware_path.setText(pup)
                try:
                    self.update_pup_info(pup)
                except Exception:
                    pass
            usb_dir = (fw.get('usb_dir') or '').strip()
            if usb_dir and hasattr(self, 'usb_dir_input'):
                self.usb_dir_input.setText(usb_dir)
            
            # Memória
            mem_gb = float(cfg.get('memory_gb', 3.0))
            try:
                self.mem_spin.setValue(mem_gb)
            except Exception:
                pass
            
            # HDD
            hdd = cfg.get('hdd') or {}
            path = (hdd.get('path') or '').strip()
            if path and hasattr(self, 'hdd_path'):
                self.hdd_path.setText(path)
            size_gb = int(hdd.get('size_gb', 20))
            try:
                if hasattr(self, 'hdd_size_gb'):
                    self.hdd_size_gb.setValue(size_gb)
            except Exception:
                pass
            
            # Gráficos
            gfx = cfg.get('graphics') or {}
            def set_combo(combo, value):
                if not hasattr(self, combo):
                    return
                cb = getattr(self, combo)
                val = (value or '').strip()
                if not val:
                    return
                idx = cb.findText(val)
                if idx >= 0:
                    cb.setCurrentIndex(idx)
                else:
                    cb.addItem(val)
                    cb.setCurrentText(val)
            set_combo('gfx_api_combo', gfx.get('api'))
            set_combo('render_combo', gfx.get('render_mode'))
            set_combo('filter_combo', gfx.get('filtering'))
            set_combo('res_combo', gfx.get('resolution'))
            if hasattr(self, 'osd_checkbox'):
                self.osd_checkbox.setChecked(bool(gfx.get('osd', False)))
            
            # Processamento
            proc = cfg.get('processing') or {}
            if hasattr(self, 'clock_spin'):
                try:
                    self.clock_spin.setValue(int(proc.get('clock_percent', 100)))
                except Exception:
                    pass
            if hasattr(self, 'ps2ee_checkbox'):
                self.ps2ee_checkbox.setChecked(bool(proc.get('ps2_ee', False)))
        except Exception:
            # Silenciosamente ignora erros de parsing/casting individuais
            pass

    def populate_gpu_list(self):
        """Popula lista de GPUs disponíveis"""
        # Simula detecção de GPUs (substitua por detecção real)
        gpus = [
            "NVIDIA GeForce RTX 4090",
            "NVIDIA GeForce RTX 4080",
            "AMD Radeon RX 7900 XTX",
            "Intel Arc A770"
        ]
        self.gpu_combo.addItems(gpus)
    
    def populate_drive_list(self):
        """Popula lista de drives de disco disponíveis"""
        # Simula detecção de drives (substitua por detecção real)
        drives = []
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            drive_path = f"{letter}:\\"
            if os.path.exists(drive_path):
                drives.append(f"Drive {letter}: ({drive_path})")
        
        if not drives:
            drives.append("Nenhum drive detectado")
        
        self.drive_combo.addItems(drives)
    
    def validate_model(self):
        """Valida o modelo do PS3"""
        model = self.model_input.text().strip()
        if not model:
            QMessageBox.warning(self, "Aviso", "Digite um modelo para validar")
            return
        
        self.validate_btn.setEnabled(False)
        self.validation_status.setText("Validando...")
        self.validation_status.setStyleSheet("color: orange;")
        
        self.validator_thread = PS3ModelValidator(model)
        self.validator_thread.validation_complete.connect(self.on_validation_complete)
        self.validator_thread.start()
    
    def on_validation_complete(self, success: bool, info: str):
        """Callback da validação do modelo"""
        self.validate_btn.setEnabled(True)
        
        if success:
            try:
                model_data = info if isinstance(info, dict) else json.loads(info)
            except Exception as e:
                self.validation_status.setText(f"✗ Erro na validação: {e}")
                self.validation_status.setStyleSheet("color: red;")
                self.console_widget.set_console_type("fat")
                # Desabilita ações quando inválido
                if hasattr(self, 'power_btn'):
                    self.power_btn.setChecked(False)
                    self.power_btn.setEnabled(False)
                    self.power_btn.setText("Power\nOn")
                if hasattr(self, 'disc_btn'):
                    self.disc_btn.setChecked(False)
                    self.disc_btn.setEnabled(False)
                    self.disc_btn.setText("Injetar\nDisco")
                return
            self.validation_status.setText(f"✓ {model_data['description']}")
            self.validation_status.setStyleSheet("color: green;")
            self.console_widget.set_console_type(model_data['type'])
            # Atualiza a imagem do console baseada no tipo
            self.update_console_image(model_data['type'])
            # Habilita ações ao validar com sucesso
            if hasattr(self, 'power_btn'):
                self.power_btn.setEnabled(True)
            if hasattr(self, 'disc_btn'):
                self.disc_btn.setEnabled(True)
        else:
            self.validation_status.setText(f"✗ {info}")
            self.validation_status.setStyleSheet("color: red;")
            self.console_widget.set_console_type("fat")  # default
            # Desabilita ações quando inválido
            if hasattr(self, 'power_btn'):
                self.power_btn.setChecked(False)
                self.power_btn.setEnabled(False)
                self.power_btn.setText("Power\nOn")
            if hasattr(self, 'disc_btn'):
                self.disc_btn.setChecked(False)
                self.disc_btn.setEnabled(False)
                self.disc_btn.setText("Injetar\nDisco")
    
    def browse_firmware_file(self):
        path, _ = QFileDialog.getOpenFileName(self, t('file.open'), os.getcwd(), t('file.ps3_firmware_filter'))
        if path:
            if hasattr(self, 'firmware_path'):
                self.firmware_path.setText(path)
            self.update_pup_info(path)

    def update_pup_info(self, path: str = None):
        """Valida e exibe informações do PUP em tempo real."""
        try:
            pup_path = ''
            if path is not None:
                pup_path = (path or '').strip()
            elif hasattr(self, 'firmware_path'):
                try:
                    pup_path = (self.firmware_path.text() or '').strip()
                except Exception:
                    pup_path = ''
            if not pup_path:
                self.pup_is_valid = False
                if hasattr(self, 'pup_info_label'):
                    self.pup_info_label.setText("Nenhum firmware selecionado")
                    self.pup_info_label.setStyleSheet("color: gray;")
                return
            # Checagem básica de extensão
            ext_ok = pup_path.lower().endswith('.pup')
            # Checagem de existência e tamanho
            if not os.path.isfile(pup_path):
                self.pup_is_valid = False
                if hasattr(self, 'pup_info_label'):
                    self.pup_info_label.setText("Caminho inválido. Arquivo não encontrado.")
                    self.pup_info_label.setStyleSheet("color: red;")
                return
            size = os.path.getsize(pup_path)
            zero_file = False
            try:
                with open(pup_path, 'rb') as f:
                    chunk = f.read(16384)
                    zero_file = (chunk == b"\x00" * len(chunk))
            except Exception:
                pass
            # Heurística de versão pelo nome do arquivo
            import re as _re
            fname = os.path.basename(pup_path)
            m = _re.search(r"(\d+\.\d+)", fname)
            version_hint = m.group(1) if m else "?"
            size_mb = size / (1024 * 1024)
            details = [
                f"Arquivo: {fname}",
                f"Tamanho: {size_mb:.2f} MB",
                f"Extensão: {'.PUP' if ext_ok else os.path.splitext(fname)[1]}",
                f"Versão (aprox. pelo nome): {version_hint}",
            ]
            valid = ext_ok and size > 0 and not zero_file
            self.pup_is_valid = bool(valid)
            if valid:
                if hasattr(self, 'pup_info_label'):
                    if hasattr(self, 'pup_info_label'):
                        self.pup_info_label.setText("\n".join(["✓ Firmware válido"] + details))
                        self.pup_info_label.setStyleSheet("color: green;")
            else:
                reasons = []
                if not ext_ok: reasons.append("extensão não é .PUP")
                if size == 0: reasons.append("arquivo com tamanho 0")
                if zero_file: reasons.append("conteúdo aparenta ser vazio (apenas zeros)")
                if hasattr(self, 'pup_info_label'):
                    self.pup_info_label.setText("\n".join(["✗ Firmware suspeito: "+ ", ".join(reasons)] + details))
                    self.pup_info_label.setStyleSheet("color: red;")
        except Exception:
            # Falha silenciosa para não quebrar a UI
            self.pup_is_valid = False
            try:
                if hasattr(self, 'pup_info_label'):
                    self.pup_info_label.setText("Falha ao ler informações do PUP")
                    self.pup_info_label.setStyleSheet("color: orange;")
            except Exception:
                pass

    def open_usb_dir(self):
        """Abre a pasta do pendrive virtual no Explorer."""
        try:
            # Preferir a última pasta utilizada pelo ModulesLoader
            target = None
            try:
                target = self.modules_loader.get_last_usb_dir()
            except Exception:
                target = None
            if not target and hasattr(self, 'usb_dir_input'):
                text = (self.usb_dir_input.text() or '').strip()
                if text:
                    target = os.path.abspath(text)
                    # Cria se não existir
                    try:
                        os.makedirs(target, exist_ok=True)
                    except Exception:
                        pass
            if not target:
                QMessageBox.warning(self, t('usb.open_failed_title'), t('usb.open_failed', error='Path vazio'))
                return
            import subprocess
            try:
                subprocess.Popen(['explorer', target])
            except Exception as e:
                QMessageBox.warning(self, t('usb.open_failed_title'), t('usb.open_failed', error=str(e)))
        except Exception as e:
            QMessageBox.warning(self, t('usb.open_failed_title'), t('usb.open_failed', error=str(e)))

    def start_recovery_mode(self):
        """Inicia o Recovery Mode"""
        if hasattr(self, 'recovery_thread') and self.recovery_thread and self.recovery_thread.isRunning():
            QMessageBox.information(self, "Recovery Mode", "Uma inicialização de Recovery já está em andamento.")
            return
        
        pup = (self.firmware_path.text().strip() or None) if hasattr(self, 'firmware_path') else None
        usb_dir = (self.usb_dir_input.text().strip() or None) if hasattr(self, 'usb_dir_input') else None
        if pup and not getattr(self, 'pup_is_valid', False):
            QMessageBox.warning(self, "Recovery Mode", "O arquivo PUP parece inválido. Corrija antes de continuar.")
            return
        
        if hasattr(self, 'start_recovery_btn'):
            self.start_recovery_btn.setEnabled(False)
        
        # Diálogo de progresso indeterminado
        self.progress_dialog = QProgressDialog("Iniciando Recovery Mode...", None, 0, 0, self)
        self.progress_dialog.setWindowTitle("Recovery Mode")
        self.progress_dialog.setWindowModality(Qt.ApplicationModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.show()
        
        # Thread para não travar a UI
        self.recovery_thread = RecoveryBootThread(self.modules_loader, pup, usb_dir)
        self.recovery_thread.success.connect(self.on_recovery_success)
        self.recovery_thread.error.connect(self.on_recovery_error)
        self.recovery_thread.finished.connect(self.on_recovery_finished)
        self.recovery_thread.start()

    def on_recovery_success(self):
        try:
            self.recovery_started.emit()
            QMessageBox.information(self, "Recovery Mode", "Recovery Mode iniciado com sucesso!")
        except Exception:
            pass

    def on_recovery_error(self, message: str):
        QMessageBox.critical(self, "Erro", f"Erro ao iniciar Recovery Mode: {message}")

    def on_recovery_finished(self):
        if hasattr(self, 'start_recovery_btn'):
            self.start_recovery_btn.setEnabled(True)
        if self.progress_dialog:
            self.progress_dialog.close()
            self.progress_dialog = None
        self.recovery_thread = None


class RecoveryModeWidget(QWidget):
    """Widget para o Recovery Mode com operações de VFlash"""

    def __init__(self):
        super().__init__()
        self.loader: ModulesLoader | None = None
        self._vflash_path = None
        self._active_ros = None
        self.setup_ui()

    def set_loader(self, loader: ModulesLoader):
        self.loader = loader
        try:
            self._refresh_vflash_info()
        except Exception:
            pass

    def setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("PS3 Recovery Mode")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #00ff00; background-color: black; padding: 10px;")
        layout.addWidget(title)

        self.console_output = QTextEdit()
        self.console_output.setStyleSheet(
            """
            QTextEdit {
                background-color: black;
                color: #00ff00;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
            """
        )
        self.console_output.setReadOnly(True)
        layout.addWidget(self.console_output)

        info_row = QHBoxLayout()
        self.lbl_vflash = QLabel("VFlash: (desconhecido)")
        self.lbl_ros = QLabel("ROS ativo: -")
        info_row.addWidget(self.lbl_vflash)
        info_row.addStretch(1)
        info_row.addWidget(self.lbl_ros)
        layout.addLayout(info_row)

        vflash_actions = QHBoxLayout()
        self.btn_refresh_info = QPushButton("Atualizar Info")
        self.btn_open_folder = QPushButton("Abrir Pasta")
        self.btn_format = QPushButton("Formatar VFlash")
        self.btn_mount = QPushButton("Montar VFlash")
        vflash_actions.addWidget(self.btn_refresh_info)
        vflash_actions.addWidget(self.btn_open_folder)
        vflash_actions.addStretch(1)
        vflash_actions.addWidget(self.btn_format)
        vflash_actions.addWidget(self.btn_mount)
        layout.addLayout(vflash_actions)

        clean_row = QHBoxLayout()
        self.btn_clean_devflash = QPushButton("Limpar dev_flash")
        self.btn_clean_devflash2 = QPushButton("Limpar dev_flash2")
        self.btn_clean_devflash3 = QPushButton("Limpar dev_flash3")
        self.btn_clean_all = QPushButton("Limpar Tudo")
        clean_row.addWidget(self.btn_clean_devflash)
        clean_row.addWidget(self.btn_clean_devflash2)
        clean_row.addWidget(self.btn_clean_devflash3)
        clean_row.addStretch(1)
        clean_row.addWidget(self.btn_clean_all)
        layout.addLayout(clean_row)

        ros_row = QHBoxLayout()
        self.btn_ros0 = QPushButton("Selecionar ROS0")
        self.btn_ros1 = QPushButton("Selecionar ROS1")
        self.btn_verify = QPushButton("Verificar LV0/Appldr")
        ros_row.addWidget(self.btn_ros0)
        ros_row.addWidget(self.btn_ros1)
        ros_row.addStretch(1)
        ros_row.addWidget(self.btn_verify)
        layout.addLayout(ros_row)

        self.btn_refresh_info.clicked.connect(self._refresh_vflash_info)
        self.btn_open_folder.clicked.connect(self._open_vflash_folder)
        self.btn_format.clicked.connect(self._on_format_vflash)
        self.btn_mount.clicked.connect(self._on_mount_vflash)
        self.btn_clean_devflash.clicked.connect(lambda: self._on_clean_partition("dev_flash"))
        self.btn_clean_devflash2.clicked.connect(lambda: self._on_clean_partition("dev_flash2"))
        self.btn_clean_devflash3.clicked.connect(lambda: self._on_clean_partition("dev_flash3"))
        self.btn_clean_all.clicked.connect(self._on_clean_all)
        self.btn_ros0.clicked.connect(lambda: self._on_select_ros("ros0"))
        self.btn_ros1.clicked.connect(lambda: self._on_select_ros("ros1"))
        self.btn_verify.clicked.connect(self._on_verify_lv0_appldr)

        self._append("PS3 System Recovery Mode\n========================\n")
        self._append("Operações de VFlash disponíveis.\n")
        self._refresh_vflash_info()

    def _append(self, text: str):
        try:
            cur = self.console_output.toPlainText()
            self.console_output.setPlainText(cur + ("" if cur.endswith("\n") else "\n") + text)
            self.console_output.moveCursor(self.console_output.textCursor().End)
        except Exception:
            pass

    def _require_loader(self) -> bool:
        if self.loader is None:
            self._append("[VFLASH] Loader não definido")
            return False
        return True

    def _refresh_vflash_info(self):
        if not self.loader:
            self.lbl_vflash.setText("VFlash: (loader não definido)")
            self.lbl_ros.setText("ROS ativo: -")
            return
        try:
            info = self.loader.get_vflash_info()
            base = info.get("path") if info else None
            self._vflash_path = base
            parts = info.get("partitions", []) if info else []
            self.lbl_vflash.setText(f"VFlash: {base if base else '(não inicializado)'} | Partições: {', '.join(parts) if parts else '-'}")
            active = getattr(self.loader, "_active_ros", None)
            self._active_ros = active
            self.lbl_ros.setText(f"ROS ativo: {active.upper() if active else '-'}")
        except Exception as e:
            self._append(f"[VFLASH] Erro ao obter informações: {e}")

    def _open_vflash_folder(self):
        path = self._vflash_path
        if not path or not os.path.exists(path):
            self._append("[VFLASH] Pasta do VFlash não encontrada")
            return
        try:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
            self._append(f"[VFLASH] Abrindo pasta: {path}")
        except Exception as e:
            self._append(f"[VFLASH] Erro ao abrir pasta: {e}")

    def _on_format_vflash(self):
        if not self._require_loader():
            return
        try:
            self.loader.format_virtual_flash()
            self._append("[VFLASH] Formatação concluída")
            self._refresh_vflash_info()
        except Exception as e:
            self._append(f"[VFLASH] Erro ao formatar: {e}")

    def _on_mount_vflash(self):
        if not self._require_loader():
            return
        try:
            if self.loader.mount_virtual_flash():
                self._append("[VFLASH] Partições montadas")
                self._refresh_vflash_info()
            else:
                self._append("[VFLASH] Falha ao montar VFlash")
        except Exception as e:
            self._append(f"[VFLASH] Erro ao montar: {e}")

    def _on_clean_partition(self, partition: str):
        if not self._require_loader():
            return
        try:
            if self.loader.clean_vflash_partition(partition):
                self._append(f"[VFLASH] Partição limpa: {partition}")
            else:
                self._append(f"[VFLASH] Falha ao limpar: {partition}")
        except Exception as e:
            self._append(f"[VFLASH] Erro ao limpar {partition}: {e}")

    def _on_clean_all(self):
        if not self._require_loader():
            return
        try:
            if self.loader.clean_all_vflash_partitions():
                self._append("[VFLASH] Todas as partições foram limpas")
            else:
                self._append("[VFLASH] Falha ao limpar todas as partições")
        except Exception as e:
            self._append(f"[VFLASH] Erro ao limpar tudo: {e}")

    def _on_select_ros(self, preferred: str):
        if not self._require_loader():
            return
        try:
            sel = self.loader.select_ros_slot(preferred=preferred)
            if sel:
                self._append(f"[ROS] Selecionado: {sel.upper()}")
            else:
                self._append("[ROS] Nenhum slot válido disponível")
            self._refresh_vflash_info()
        except Exception as e:
            self._append(f"[ROS] Erro ao selecionar slot: {e}")

    def _on_verify_lv0_appldr(self):
        if not self._require_loader():
            return
        try:
            ok = self.loader._verify_lv0_and_appldr()
            self._append("[SEC] Verificação LV0/Appldr: OK" if ok else "[SEC] Verificação LV0/Appldr: FALHOU")
        except Exception as e:
            self._append(f"[SEC] Erro na verificação: {e}")


class ScriptingRunThread(QThread):
    started_signal = Signal()
    finished_signal = Signal()
    error_signal = Signal(str)

    def __init__(self, engine: ScriptingEngine, code: str, script_path: str | None = None):
        super().__init__()
        self.engine = engine
        self.code = code
        self.script_path = script_path

    def run(self):
        self.started_signal.emit()
        try:
            self.engine.run(self.code, script_path=self.script_path)
        except Exception as e:
            self.error_signal.emit(str(e))
        finally:
            self.finished_signal.emit()


class ScriptingWidget(QWidget):
    """Painel de scripting Lua (via 'lupa')"""
    def __init__(self, loader: ModulesLoader):
        super().__init__()
        self.loader = loader
        self.engine = ScriptingEngine(loader, on_output=self._append_output)
        self._runner: ScriptingRunThread | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel(t('scripting.title') if callable(t) else 'Scripting')
        title.setFont(QFont('Arial', 16, QFont.Bold))
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(title)

        splitter = QSplitter(Qt.Vertical)
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText('-- Lua script here. Example:\n-- gscx.load_modules()\n-- gscx.boot_recovery()')
        self.editor.setStyleSheet("QPlainTextEdit { font-family: 'Consolas, Courier New, monospace'; font-size: 12px; }")
        self.highlighter = LuaHighlighter(self.editor.document())
        splitter.addWidget(self.editor)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet("QTextEdit { background: #111; color: #8f8; font-family: 'Consolas, Courier New, monospace'; font-size: 12px; }")
        splitter.addWidget(self.output)
        splitter.setSizes([300, 200])
        layout.addWidget(splitter)

        btn_row = QHBoxLayout()
        self.btn_run = QPushButton(t('scripting.run'))
        self.btn_run_sel = QPushButton(t('scripting.run_selection'))
        self.btn_stop = QPushButton(t('scripting.stop'))
        self.btn_clear = QPushButton(t('scripting.clear'))
        self.btn_load = QPushButton(t('scripting.load'))
        self.btn_run_file = QPushButton(t('scripting.run_file'))
        self.btn_save = QPushButton(t('scripting.save'))
        btn_row.addWidget(self.btn_run)
        btn_row.addWidget(self.btn_run_sel)
        btn_row.addWidget(self.btn_stop)
        btn_row.addWidget(self.btn_clear)
        btn_row.addStretch(1)
        btn_row.addWidget(self.btn_load)
        btn_row.addWidget(self.btn_run_file)
        btn_row.addWidget(self.btn_save)
        layout.addLayout(btn_row)

        self.btn_stop.setEnabled(False)

        self.btn_run.clicked.connect(self._on_run)
        self.btn_run_sel.clicked.connect(self._on_run_selection)
        self.btn_stop.clicked.connect(self._on_stop)
        self.btn_clear.clicked.connect(self._on_clear_output)
        self.btn_load.clicked.connect(self._on_load)
        self.btn_run_file.clicked.connect(self._on_run_file)
        self.btn_save.clicked.connect(self._on_save)

        if not self.engine.available():
            QMessageBox.warning(self, t('general.warning'), t('scripting.lua_missing'))
            # Disable scripting functionality if Lua is not available
            self.btn_run.setEnabled(False)
            self.btn_run_sel.setEnabled(False)
            self.btn_run_file.setEnabled(False)
            self.editor.setPlaceholderText('Lua runtime not available. Install lupa to enable scripting.')

    def _append_output(self, text: str):
        try:
            self.output.moveCursor(self.output.textCursor().End)
            self.output.insertPlainText(text)
            self.output.moveCursor(self.output.textCursor().End)
        except Exception:
            pass

    def _on_run(self):
        if self._runner and self._runner.isRunning():
            QMessageBox.information(self, t('scripting.title'), t('scripting.running'))
            return
        code = self.editor.toPlainText()
        if not code.strip():
            code = "print('Hello from Lua'); gscx.load_modules()"
        self.output.clear()
        try:
            self._runner = ScriptingRunThread(self.engine, code)
            self._runner.started_signal.connect(self._on_started)
            self._runner.finished_signal.connect(self._on_finished)
            self._runner.error_signal.connect(lambda e: self._append_output('[Lua][Error] ' + str(e) + '\n'))
            self._runner.started_signal.connect(lambda: self._append_output('[Lua] ' + t('scripting.running') + '\n'))
            self._runner.finished_signal.connect(lambda: self._append_output('[Lua] ' + t('scripting.completed') + '\n'))
            self._runner.start()
        except Exception as e:
            QMessageBox.critical(self, t('general.error'), str(e))

    def _on_run_selection(self):
        if self._runner and self._runner.isRunning():
            QMessageBox.information(self, t('scripting.title'), t('scripting.running'))
            return
        cursor = self.editor.textCursor()
        sel = cursor.selectedText().replace('\u2029', '\n') if cursor.hasSelection() else ''
        if not sel.strip():
            QMessageBox.information(self, t('scripting.title'), t('scripting.run_selection'))
            return
        try:
            self._runner = ScriptingRunThread(self.engine, sel)
            self._runner.started_signal.connect(self._on_started)
            self._runner.finished_signal.connect(self._on_finished)
            self._runner.error_signal.connect(lambda e: self._append_output('[Lua][Error] ' + str(e) + '\n'))
            self._runner.started_signal.connect(lambda: self._append_output('[Lua] ' + t('scripting.running') + '\n'))
            self._runner.finished_signal.connect(lambda: self._append_output('[Lua] ' + t('scripting.completed') + '\n'))
            self._runner.start()
        except Exception as e:
            QMessageBox.critical(self, t('general.error'), str(e))

    def _on_run_file(self):
        if self._runner and self._runner.isRunning():
            QMessageBox.information(self, t('scripting.title'), t('scripting.running'))
            return
        filters = f"{t('file.lua_filter')};;{t('file.all_files')}"
        path, _ = QFileDialog.getOpenFileName(self, t('file.open'), '', filters)
        if not path:
            return
        self.output.clear()
        try:
            # Run file via engine (preserves working dir semantics)
            self._runner = ScriptingRunThread(self.engine, f"-- file: {os.path.basename(path)}\n", script_path=path)
            self._runner.started_signal.connect(self._on_started)
            self._runner.finished_signal.connect(self._on_finished)
            self._runner.error_signal.connect(lambda e: self._append_output('[Lua][Error] ' + str(e) + '\n'))
            self._runner.started_signal.connect(lambda: self._append_output('[Lua] ' + t('scripting.running') + '\n'))
            self._runner.finished_signal.connect(lambda: self._append_output('[Lua] ' + t('scripting.completed') + '\n'))
            # Use engine.run_file inside the thread by passing script_path; thread will call engine.run(...)
            self._runner.start()
            # Additionally, kick a direct run_file when thread starts
            QTimer.singleShot(0, lambda: self.engine.run_file(path))
        except Exception as e:
            QMessageBox.critical(self, t('general.error'), str(e))

    def _on_stop(self):
        """Stop the currently running script with proper cleanup"""
        if self._runner and self._runner.isRunning():
            try:
                self._runner.terminate()
                if not self._runner.wait(3000):  # Wait up to 3 seconds
                    self._runner.kill()  # Force kill if needed
                self._append_output('[Lua] ' + t('scripting.stopped') + '\n')
            except Exception as e:
                self._append_output(f'[Lua][Error] Failed to stop script: {e}\n')
            finally:
                self._on_finished()

    def _on_clear_output(self):
        """Clear the output console"""
        self.output.clear()

    def _on_started(self):
        # Disable run buttons during execution
        self.btn_run.setEnabled(False)
        self.btn_run_sel.setEnabled(False)
        self.btn_run_file.setEnabled(False)
        self.btn_stop.setEnabled(True)

    def _on_finished(self):
        self.btn_run.setEnabled(True)
        self.btn_run_sel.setEnabled(True)
        self.btn_run_file.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self._runner = None

    def _on_load(self):
        """Load a Lua script file into the editor"""
        filters = f"{t('file.lua_filter')};;{t('file.all_files')}"
        path, _ = QFileDialog.getOpenFileName(self, t('file.open'), '', filters)
        if not path:
            return
        
        # Validate file exists and is readable
        if not os.path.exists(path):
            QMessageBox.critical(self, t('general.error'), f'File not found: {path}')
            return
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                self.editor.setPlainText(content)
                self._append_output(f'[Editor] Loaded script: {os.path.basename(path)}\n')
        except Exception as e:
            QMessageBox.critical(self, t('general.error'), t('scripting.load_error') + f"\n{e}")

    def _on_save(self):
        """Save the current script to a file"""
        filters = f"{t('file.lua_filter')};;{t('file.all_files')}"
        path, _ = QFileDialog.getSaveFileName(self, t('file.save'), 'script.lua', filters)
        if not path:
            return
            
        # Ensure .lua extension if not provided
        if not path.lower().endswith('.lua'):
            path += '.lua'
            
        try:
            content = self.editor.toPlainText()
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            self._append_output(f'[Editor] Saved script: {os.path.basename(path)}\n')
        except Exception as e:
            QMessageBox.critical(self, t('general.error'), f'Failed to save script: {e}')


class GSCXMainWindow(QMainWindow):
    """Janela principal do GSCX"""
    
    def __init__(self):
        super().__init__()
        self.modules_loader = ModulesLoader(self.on_log_message)
        # Definir ícone da janela
        try:
            app_dir = os.path.dirname(__file__)
            icon_path = os.path.join(app_dir, 'icons', 'app_icon.svg')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass
        self.setup_ui()
        self.setup_toolbars()
        self.setup_status_bar()
        # Carregar módulos automaticamente (sem botão dedicado)
        QTimer.singleShot(100, self._auto_load_modules)
    
    def setup_ui(self):
        self.setWindowTitle("GSCX - PlayStation 3 Emulator")
        self.setMinimumSize(1200, 800)
        
        # Widget central com stack
        self.central_stack = QStackedWidget()
        
        # Páginas
        self.setup_page = PS3SetupWidget(self.modules_loader)  # Home
        self.recovery_page = RecoveryModeWidget()
        # Fornece o loader para o Recovery via setter, mantendo compatibilidade do construtor
        try:
            self.recovery_page.set_loader(self.modules_loader)
        except Exception:
            pass
        self.scripting_page = ScriptingWidget(self.modules_loader)
        
        self.central_stack.addWidget(self.setup_page)
        self.central_stack.addWidget(self.recovery_page)
        self.central_stack.addWidget(self.scripting_page)
        
        # Novas páginas
        self.storage_page = QWidget()
        sp_layout = QVBoxLayout(self.storage_page)
        sp_layout.addWidget(QLabel("Storage"))
        sp_layout.addWidget(QLabel("Configurar armazenamento virtual (em desenvolvimento)"))
        sp_layout.addStretch()
        
        self.tweak_hw_page = QWidget()
        th_layout = QVBoxLayout(self.tweak_hw_page)
        th_layout.addWidget(QLabel("Tweak Virtual Hardware"))
        th_layout.addWidget(QCheckBox("Antena Wi‑Fi"))
        th_layout.addWidget(QCheckBox("Antena Bluetooth"))
        oc_layout = QHBoxLayout()
        oc_layout.addWidget(QLabel("Overclock (MHz):"))
        self.oc_spin = QSpinBox()
        self.oc_spin.setRange(1600, 5000)
        self.oc_spin.setValue(3200)
        oc_layout.addWidget(self.oc_spin)
        th_layout.addLayout(oc_layout)
        th_layout.addStretch()
        
        self.games_page = QWidget()
        gp_layout = QVBoxLayout(self.games_page)
        gp_layout.addWidget(QLabel("Games Folder"))
        gp_layout.addWidget(QLabel("Gerencie pastas de jogos (em desenvolvimento)"))
        gp_layout.addStretch()
        
        self.logs_page = QPlainTextEdit()
        self.logs_page.setReadOnly(True)
        
        self.debug_console_page = QPlainTextEdit()
        self.debug_console_page.setReadOnly(True)
        self.debug_console_page.setStyleSheet("font-family: Consolas, monospace;")
        
        self.central_stack.addWidget(self.storage_page)
        self.central_stack.addWidget(self.tweak_hw_page)
        self.central_stack.addWidget(self.games_page)
        self.central_stack.addWidget(self.logs_page)
        self.central_stack.addWidget(self.debug_console_page)
        
        # Barra lateral
        self.left_nav = QListWidget()
        self.left_nav.addItems(["Home", "Storage", "Tweak Virtual Hardware", "Games Folder", "Logs", "Console de Debug"])
        self.left_nav.setFixedWidth(220)
        
        self._nav_widgets = [self.setup_page, self.storage_page, self.tweak_hw_page, self.games_page, self.logs_page, self.debug_console_page]
        self.left_nav.currentRowChanged.connect(lambda row: self.central_stack.setCurrentWidget(self._nav_widgets[row]) if 0 <= row < len(self._nav_widgets) else None)
        self.left_nav.setCurrentRow(0)
        
        container = QWidget()
        hbox = QHBoxLayout(container)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(self.left_nav)
        hbox.addWidget(self.central_stack)
        self.setCentralWidget(container)
    
    def setup_toolbars(self):
        """Configura a barra superior (menus)"""
        top_toolbar = self.addToolBar("Principal")
        top_toolbar.setMovable(False)
        
        # Emulação (dropdown)
        emu_btn = QToolButton(self)
        emu_btn.setText("Emulação")
        emu_btn.setPopupMode(QToolButton.MenuButtonPopup)
        emu_menu = QMenu("Emulação", self)
        
        act_change_controls = emu_menu.addAction("Trocar Controles")
        act_change_controls.triggered.connect(self._emulation_change_controls)
        emu_menu.addSeparator()
        act_power_on = emu_menu.addAction("Ligar Console")
        act_power_on.triggered.connect(self._emulation_power_on)
        act_reset = emu_menu.addAction("Resetar Console")
        act_reset.triggered.connect(self._emulation_reset)
        act_power_off = emu_menu.addAction("Desligar Console")
        act_power_off.triggered.connect(self._emulation_power_off)
        emu_menu.addSeparator()
        act_start_recovery = emu_menu.addAction("Iniciar Recovery Mode (simular segurar)")
        act_start_recovery.triggered.connect(self._emulation_start_recovery)
        emu_menu.addSeparator()
        act_change_disk = emu_menu.addAction("Mudar Disco (virtual)")
        act_change_disk.triggered.connect(self._emulation_change_disk)
        act_eject = emu_menu.addAction("Ejetar Disco (virtual)")
        act_eject.triggered.connect(self._emulation_eject_disk)
        act_insert = emu_menu.addAction("Inserir Disco (virtual)")
        act_insert.triggered.connect(self._emulation_insert_disk)
        
        emu_btn.setMenu(emu_menu)
        top_toolbar.addWidget(emu_btn)
        
        top_toolbar.addSeparator()
        
        # Configurações (dropdown) com idiomas e salvar config
        cfg_btn = QToolButton(self)
        cfg_btn.setText("Configurações")
        cfg_btn.setPopupMode(QToolButton.MenuButtonPopup)
        cfg_menu = QMenu("Configurações", self)
        
        # Submenu Idioma
        lang_menu = cfg_menu.addMenu("Idioma")
        for code, name in LANG_DISPLAY.items():
            a = lang_menu.addAction(name)
            a.setData(code)
            a.triggered.connect(lambda checked=False, c=code: self._set_language(c))
        
        cfg_menu.addSeparator()
        # Configurações Gerais
        act_general = cfg_menu.addAction("Configurações Gerais")
        act_general.triggered.connect(self._open_general_settings)
        cfg_menu.addSeparator()
        act_save = cfg_menu.addAction("Salvar Configuração")
        act_save.triggered.connect(lambda: getattr(self.setup_page, 'save_configuration', lambda: None)())
        
        cfg_btn.setMenu(cfg_menu)
        top_toolbar.addWidget(cfg_btn)
        
        top_toolbar.addSeparator()
        
        # Páginas principais (removido Setup; navegação agora pela barra lateral)
        scripting_action = QAction(t('scripting.title'), self)
        scripting_action.triggered.connect(lambda: self.central_stack.setCurrentWidget(self.scripting_page))
        top_toolbar.addAction(scripting_action)
        
        top_toolbar.addSeparator()
        
        # Help
        help_btn = QToolButton(self)
        help_btn.setText("Help")
        help_btn.setPopupMode(QToolButton.MenuButtonPopup)
        help_menu = QMenu("Help", self)
        act_docs = help_menu.addAction("Documentação")
        act_docs.triggered.connect(self._open_help_docs)
        act_about = help_menu.addAction("Sobre")
        act_about.triggered.connect(self._show_about)
        help_btn.setMenu(help_menu)
        top_toolbar.addWidget(help_btn)
        
        # Debug
        debug_btn = QToolButton(self)
        debug_btn.setText("Debug")
        debug_btn.setPopupMode(QToolButton.MenuButtonPopup)
        debug_menu = QMenu("Debug", self)
        act_show_log = debug_menu.addAction("Mostrar Log")
        act_show_log.triggered.connect(self._show_debug_log)
        act_reload = debug_menu.addAction("Recarregar Módulos")
        act_reload.triggered.connect(self._auto_load_modules)
        debug_btn.setMenu(debug_menu)
        top_toolbar.addWidget(debug_btn)
    
    def setup_status_bar(self):
        """Configura a barra de status"""
        self.status_label = QLabel("Ready")
        self.statusBar().addWidget(self.status_label)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.statusBar().addPermanentWidget(self.progress_bar)
    
    def on_log_message(self, message: str):
        """Callback para mensagens de log"""
        msg = message.strip()
        self.status_label.setText(msg)
        # Recovery
        try:
            self.recovery_page.console_output.append(msg)
        except Exception:
            pass
        # Scripting
        try:
            if hasattr(self, 'scripting_page') and hasattr(self.scripting_page, 'output'):
                self.scripting_page._append_output(message)
        except Exception:
            pass
        # Prefixo 0x... e mensagem formatada
        prefix = f"0x{abs(hash(msg)) & 0xFFFFFF:06X}: "
        formatted = prefix + msg
        # Logs page
        try:
            if hasattr(self, 'logs_page') and isinstance(self.logs_page, QPlainTextEdit):
                self.logs_page.appendPlainText(formatted)
        except Exception:
            pass
        # Console de Debug
        try:
            if hasattr(self, 'debug_console_page') and isinstance(self.debug_console_page, QPlainTextEdit):
                self.debug_console_page.appendPlainText(formatted)
        except Exception:
            pass
    
    def load_modules(self):
        """Carrega os módulos do emulador"""
        try:
            self.status_label.setText(t('status.loading_modules'))
            self.progress_bar.setVisible(True)
            self.modules_loader.load_default_modules()
            self.status_label.setText("Pronto")
            self.progress_bar.setVisible(False)
        except Exception as e:
            QMessageBox.critical(self, t('general.error'), t('status.load_modules_error') + f": {str(e)}")
            self.status_label.setText(t('status.load_modules_error'))
            self.progress_bar.setVisible(False)
    
    def show_gpu_info(self):
        QMessageBox.information(self, "GPU (RSX)", "Reality Synthesizer\nBaseado em NVIDIA G70")
    
    def on_language_changed(self):
        """Mantido por compatibilidade; redireciona para _set_language se existir combo antigo"""
        try:
            if hasattr(self, 'lang_combo'):
                lang_code = self.lang_combo.currentData()
                if lang_code:
                    self._set_language(lang_code)
        except Exception:
            pass

    def _set_language(self, lang_code: str):
        try:
            set_language(lang_code)
            # Atualizar interface
            self.update_ui_language()
            self.status_label.setText(f"Idioma alterado para: {LANG_DISPLAY.get(lang_code, lang_code)}")
        except Exception as e:
            QMessageBox.warning(self, t('general.warning'), f"Falha ao alterar idioma: {e}")

    def _auto_load_modules(self):
        try:
            self.status_label.setText(t('status.loading_modules'))
            self.progress_bar.setVisible(True)
            self.modules_loader.load_default_modules()
            self.status_label.setText("Pronto")
        except Exception as e:
            QMessageBox.critical(self, t('general.error'), t('status.load_modules_error') + f": {str(e)}")
        finally:
            self.progress_bar.setVisible(False)

    # Emulação handlers
    def _emulation_change_controls(self):
        QMessageBox.information(self, "Controles", "Troca de controles: em desenvolvimento")

    def _emulation_power_on(self):
        try:
            self.start_ps3_boot_sequence()
        except Exception:
            QMessageBox.information(self, "Emulação", "Console ligado (virtual)")

    def _emulation_reset(self):
        QMessageBox.information(self, "Emulação", "Console resetado (virtual)")

    def _emulation_power_off(self):
        QMessageBox.information(self, "Emulação", "Console desligado (virtual)")

    def _emulation_start_recovery(self):
        try:
            self.central_stack.setCurrentWidget(self.recovery_page)
            if hasattr(self.setup_page, 'start_recovery_mode'):
                self.setup_page.start_recovery_mode()
            else:
                QMessageBox.information(self, "Recovery Mode", "Recovery iniciado (simulado)")
        except Exception as e:
            QMessageBox.critical(self, "Recovery Mode", f"Falha ao iniciar recovery: {e}")

    def _emulation_change_disk(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecionar ISO do Jogo", "", "Arquivos ISO (*.iso);;Todos os arquivos (*)")
        if file_path:
            QMessageBox.information(self, "Disco Virtual", f"Disco alterado para: {os.path.basename(file_path)}")

    def _emulation_eject_disk(self):
        QMessageBox.information(self, "Disco Virtual", "Disco ejetado (virtual)")

    def _emulation_insert_disk(self):
        QMessageBox.information(self, "Disco Virtual", "Disco inserido (virtual)")

    def _open_help_docs(self):
        try:
            QDesktopServices.openUrl(QUrl("https://github.com/HunterTheD3V/Project-GSCX-Emulator"))
        except Exception:
            QMessageBox.information(self, "Documentação", "Abra: https://github.com/HunterTheD3V/Project-GSCX-Emulator")

    def _open_general_settings(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Configurações Gerais")
        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel("Configurações Gerais do Emulador"))
        layout.addWidget(QCheckBox("Inicializar com a última ISO utilizada"))
        layout.addWidget(QCheckBox("Ativar telemetria anônima"))
        layout.addWidget(QCheckBox("Ativar atualizações automáticas"))
        layout.addStretch()
        btns = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Cancelar")
        btn_ok.clicked.connect(dlg.accept)
        btn_cancel.clicked.connect(dlg.reject)
        btns.addStretch()
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok)
        layout.addLayout(btns)
        dlg.exec()

    def _show_about(self):
        info = _load_app_info()
        QMessageBox.information(self, "Sobre", f"{info.get('name','GSCX')}\nVersão: {info.get('version','0.1.0')}")

    def _show_debug_log(self):
        try:
            self.recovery_page.console_output.append("[Debug] Log ativo...")
            self.central_stack.setCurrentWidget(self.recovery_page)
        except Exception:
            pass
    
    def update_ui_language(self):
        """Atualiza textos da interface com novo idioma"""
        # Implementar atualização de textos
        pass


def _load_app_info():
    import configparser, os
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    ini_path = os.path.join(ROOT_DIR, 'app.ini')
    info = {'name': 'GSCX', 'version': '0.1.0'}
    try:
        if os.path.isfile(ini_path):
            cfg = configparser.ConfigParser()
            cfg.read(ini_path, encoding='utf-8')
            sec = cfg['info'] if 'info' in cfg else {}
            def norm(v: str):
                v = (v or '').strip()
                if len(v) >= 2 and ((v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'"))):
                    v = v[1:-1]
                return v
            info['name'] = norm(sec.get('name', info['name']))
            info['version'] = norm(sec.get('version', info['version']))
    except Exception:
        pass
    return info


def create_gui_app(argv=None):
    """Cria e executa a aplicação GUI"""
    app = QApplication(argv or sys.argv)
    _info = _load_app_info()
    app.setApplicationName(_info.get('name') or "GSCX")
    app.setApplicationVersion((_info.get('version') or '').strip())
    
    # Criar e mostrar splash screen com banner GSCX
    splash = create_splash_screen()
    splash.show()
    app.processEvents()
    
    # Initialize language from user_config.json
    try:
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        cfg_path = os.path.join(root, 'user_config.json')
        lang = 'en'
        if os.path.isfile(cfg_path):
            with open(cfg_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            lang = (cfg.get('language') or 'en').strip()
    except Exception:
        lang = 'en'
    try:
        set_language(lang)
    except Exception:
        pass
    
    # Simular carregamento
    splash.showMessage("Inicializando GSCX...", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    app.processEvents()
    
    # Criar janela principal
    window = GSCXMainWindow()
    
    # Finalizar splash e mostrar janela
    splash.showMessage("Carregamento concluído!", Qt.AlignBottom | Qt.AlignCenter, Qt.white)
    app.processEvents()
    
    # Aguardar um pouco antes de fechar o splash
    QTimer.singleShot(1500, lambda: (splash.close(), window.show()))
    
    return app.exec()

def create_splash_screen():
    """Cria a tela de splash com o banner GSCX"""
    try:
        # Caminho para o banner GSCX
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        banner_path = os.path.join(root, 'docs', 'assets', 'GSCX_banner.png')
        
        if os.path.exists(banner_path):
            pixmap = QPixmap(banner_path)
            # Redimensionar se necessário
            if pixmap.width() > 800 or pixmap.height() > 400:
                pixmap = pixmap.scaled(800, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        else:
            # Fallback: criar um banner simples se o arquivo não existir
            pixmap = QPixmap(600, 300)
            pixmap.fill(Qt.black)
            painter = QPainter(pixmap)
            painter.setPen(Qt.white)
            painter.setFont(QFont("Arial", 48, QFont.Bold))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "GSCX")
            painter.end()
        
        splash = QSplashScreen(pixmap)
        splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.SplashScreen)
        return splash
        
    except Exception as e:
        # Em caso de erro, criar splash simples
        pixmap = QPixmap(400, 200)
        pixmap.fill(Qt.darkBlue)
        painter = QPainter(pixmap)
        painter.setPen(Qt.white)
        painter.setFont(QFont("Arial", 32, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "GSCX")
        painter.end()
        
        splash = QSplashScreen(pixmap)
        splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.SplashScreen)
        return splash


# Mantém compatibilidade com a classe MainWindow original
MainWindow = GSCXMainWindow


class LuaHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = []
        # Keywords
        kw_format = QTextCharFormat()
        kw_format.setForeground(QColor('#d19a66'))
        keywords = [
            'and','break','do','else','elseif','end','false','for','function','goto','if',
            'in','local','nil','not','or','repeat','return','then','true','until','while'
        ]
        for kw in keywords:
            self.rules.append((QRegularExpression(r"\\b" + kw + r"\\b"), kw_format))
        # Single-line comments
        com_format = QTextCharFormat()
        com_format.setForeground(QColor('#5c6370'))
        self.rules.append((QRegularExpression(r"--[^\n]*"), com_format))
        # Strings
        str_format = QTextCharFormat()
        str_format.setForeground(QColor('#98c379'))
        self.rules.append((QRegularExpression(r"'(?:\\\\.|[^'\\n])*'"), str_format))
        self.rules.append((QRegularExpression(r'"(?:\\\\.|[^"\\n])*"'), str_format))

    def highlightBlock(self, text: str):
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)