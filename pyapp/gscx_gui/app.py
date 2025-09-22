import sys
import os
import argparse
import time
import configparser
from .modules_loader import ModulesLoader, ScriptingEngine
from .main_window import create_gui_app
from .i18n import set_language

# ---- Importações PySide6 para GUI ----
from PySide6.QtWidgets import (
    QApplication, QWidget, QComboBox, QPushButton,
    QVBoxLayout, QHBoxLayout, QSplashScreen, QProgressBar, QLabel
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QPainter, QFont, QColor


def load_app_info():
    """Carrega informações do app.ini"""
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    cfg = configparser.ConfigParser()
    ini_path = os.path.join(ROOT_DIR, 'app.ini')
    info = {
        'name': 'GSCX',
        'version': '0.4.1',
        'build': '',
        'description': ''
    }
    try:
        if os.path.isfile(ini_path):
            cfg.read(ini_path, encoding='utf-8')
            sec = cfg['info'] if 'info' in cfg else {}
            def norm(v: str):
                v = (v or '').strip()
                if len(v) >= 2 and ((v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'"))):
                    v = v[1:-1]
                return v
            info['name'] = norm(sec.get('name', info['name']))
            info['version'] = norm(sec.get('version', info['version']))
            info['build'] = norm(str(sec.get('build', info['build'])))
            info['description'] = norm(sec.get('description', info['description']))
    except Exception:
        pass
    return info


class LoadingProgress(QObject):
    """Gerenciador de progresso de carregamento"""
    progress_updated = Signal(int, str)  # progress, message
    loading_complete = Signal()
    
    def __init__(self):
        super().__init__()
        self.steps = [
            ("Inicializando GSCX...", 10),
            ("Verificando dependências Python...", 20),
            ("Carregando módulos do sistema...", 35),
            ("Inicializando interface gráfica...", 50),
            ("Configurando módulos de emulação...", 65),
            ("Preparando Recovery Mode HLE...", 80),
            ("Finalizando carregamento...", 95),
            ("GSCX pronto!", 100)
        ]
        self.current_step = 0
    
    def start_loading(self):
        """Inicia o processo de carregamento simulado"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.next_step)
        self.timer.start(800)  # 800ms entre cada etapa
    
    def next_step(self):
        """Avança para a próxima etapa"""
        if self.current_step < len(self.steps):
            message, progress = self.steps[self.current_step]
            self.progress_updated.emit(progress, message)
            self.current_step += 1
        else:
            self.timer.stop()
            self.loading_complete.emit()


class GSCXSplashScreen(QSplashScreen):
    """Splash screen customizado do GSCX"""
    
    def __init__(self):
        # Cria o pixmap base para o splash screen
        pixmap = QPixmap(600, 400)
        pixmap.fill(QColor(43, 43, 43))  # Cor de fundo escura
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Tenta carregar e desenhar o banner GSCX no centro
        ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        banner_path = os.path.join(ROOT_DIR, 'docs', 'assets', 'GSCX_banner.png')
        banner_drawn = False
        
        if os.path.exists(banner_path):
            banner = QPixmap(banner_path)
            if not banner.isNull():
                # Redimensiona o banner para caber bem no splash (10% maior)
                banner_scaled = banner.scaled(440, 165, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                # Centraliza o banner
                banner_x = (pixmap.width() - banner_scaled.width()) // 2
                banner_y = (pixmap.height() - banner_scaled.height()) // 2 - 30
                painter.drawPixmap(banner_x, banner_y, banner_scaled)
                banner_drawn = True
        
        # Se não conseguiu carregar o banner, desenha o texto GSCX
        if not banner_drawn:
            # Tenta carregar logo da SunFlare no topo
            sunflare_path = os.path.join(ROOT_DIR, 'docs', 'assets', 'SunFlare_Technologies.png')
            if os.path.exists(sunflare_path):
                sunflare_logo = QPixmap(sunflare_path)
                if not sunflare_logo.isNull():
                    logo_scaled = sunflare_logo.scaled(120, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    logo_x = (pixmap.width() - logo_scaled.width()) // 2
                    painter.drawPixmap(logo_x, 20, logo_scaled)
            
            # Título principal GSCX
            title_font = QFont("Arial", 32, QFont.Bold)
            painter.setFont(title_font)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(pixmap.rect().adjusted(0, 100, 0, 0), Qt.AlignCenter | Qt.AlignTop, "GSCX")
            
            # Subtítulo
            subtitle_font = QFont("Arial", 14)
            painter.setFont(subtitle_font)
            painter.setPen(QColor(200, 200, 200))
            subtitle_rect = pixmap.rect().adjusted(0, 180, 0, 0)
            painter.drawText(subtitle_rect, Qt.AlignCenter | Qt.AlignTop, "Sony's PlayStation 3 High-Level Emulator")
        
        # Versão (sempre exibida)
        version_font = QFont("Arial", 10)
        painter.setFont(version_font)
        painter.setPen(QColor(150, 150, 150))
        version_rect = pixmap.rect().adjusted(0, 0, -20, -20)
        app_info = load_app_info()
        ver = (app_info.get('version') or '').strip()
        build = (app_info.get('build') or '').strip()
        version_text = f"v{ver} (build {build})" if build else f"v{ver}"
        painter.drawText(version_rect, Qt.AlignRight | Qt.AlignBottom, version_text)
        
        painter.end()
        
        super().__init__(pixmap)
        self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(0.0)
        
        # Configura o layout para a barra de progresso
        self.setup_progress_ui()
        
        # Gerenciador de progresso
        self.progress_manager = LoadingProgress()
        self.progress_manager.progress_updated.connect(self.update_progress)
        self.progress_manager.loading_complete.connect(self.loading_finished)

    def showEvent(self, event):
        super().showEvent(event)
        # Animação de fade-in ao exibir o splash
        self._start_fade_in()

    def _start_fade_in(self):
        self._fade_in_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade_in_anim.setDuration(600)
        self._fade_in_anim.setStartValue(0.0)
        self._fade_in_anim.setEndValue(1.0)
        self._fade_in_anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._fade_in_anim.start()

    def _start_fade_out_and_launch(self):
        self._fade_out_anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade_out_anim.setDuration(450)
        self._fade_out_anim.setStartValue(self.windowOpacity())
        self._fade_out_anim.setEndValue(0.0)
        self._fade_out_anim.setEasingCurve(QEasingCurve.InOutCubic)
        self._fade_out_anim.finished.connect(self.launch_main_app)
        self._fade_out_anim.start()
    
    def setup_progress_ui(self):
        """Configura a UI da barra de progresso"""
        # Widget container para a barra de progresso
        self.progress_widget = QWidget(self)
        self.progress_widget.setGeometry(50, 320, 500, 60)
        
        layout = QVBoxLayout(self.progress_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #555;
                border-radius: 5px;
                text-align: center;
                background-color: #2b2b2b;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Label de status
        self.status_label = QLabel("Inicializando...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 12px;
                background-color: transparent;
            }
        """)
        layout.addWidget(self.status_label)
        
        self.progress_widget.show()
    
    def update_progress(self, progress: int, message: str):
        """Atualiza a barra de progresso e mensagem"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
        self.repaint()
    
    def loading_finished(self):
        """Callback quando o carregamento termina"""
        QTimer.singleShot(400, self._start_fade_out_and_launch)  # pequena pausa + fade-out antes de abrir a app principal
    
    def launch_main_app(self):
        """Lança a aplicação principal"""
        try:
            # Importa a janela principal diretamente
            from .main_window import GSCXMainWindow
            
            # Cria e mostra a janela principal
            self.main_window = GSCXMainWindow()
            self.main_window.show()
            
            # Fecha o splash screen
            self.close()
            
        except Exception as e:
            print(f"Erro ao carregar aplicação principal: {str(e)}")
            import traceback
            traceback.print_exc()
            
            self.status_label.setText(f"Erro ao carregar: {str(e)}")
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #555;
                    border-radius: 5px;
                    text-align: center;
                    background-color: #2b2b2b;
                    color: white;
                    font-weight: bold;
                }
                QProgressBar::chunk {
                    background-color: #f44336;
                    border-radius: 3px;
                }
            """)
            QTimer.singleShot(3000, self.close)  # Fecha após 3s em caso de erro
    
    def start_loading(self):
        """Inicia o processo de carregamento"""
        self.progress_manager.start_loading()


def create_gui_with_splash():
    """Cria e executa o GUI do GSCX com splash screen"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    app_info = load_app_info()
    app.setApplicationName(app_info.get('name') or "GSCX")
    app.setApplicationVersion((app_info.get('version') or '').strip())
    
    # Aplica tema escuro global
    app.setStyleSheet("""
        QWidget {
            background-color: #2b2b2b;
            color: white;
        }
    """)
    
    # Cria e mostra o splash screen
    splash = GSCXSplashScreen()
    splash.show()
    
    # Inicia o carregamento
    splash.start_loading()
    
    return app.exec()


def main(argv=None):
    parser = argparse.ArgumentParser(description="GSCX GUI/CLI - Boot Recovery HLE")
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--load-default", action="store_true", help="Carrega DLLs dos diretórios padrão de build")
    g.add_argument("--bundle", type=str, help="Caminho para bundle GSCore (.gscb)")
    parser.add_argument("--boot-recovery", action="store_true", help="Invoca GSCX_RecoveryEntry após carregar os módulos")
    parser.add_argument("--script", type=str, help="Executa um script Lua (requer 'lupa')")
    parser.add_argument("--lang", type=str, choices=["en","es","pt"], help="Idioma da interface (GUI) e mensagens")
    parser.add_argument("--gui", action="store_true", help="Inicia interface gráfica")
    parser.add_argument("--no-gui", action="store_true", help="Força modo CLI")
    args = parser.parse_args(argv)

    if args.lang:
        try:
            set_language(args.lang)
        except Exception:
            pass

    def on_log(msg: str):
        print(msg, end="")

    # Se --gui foi especificado ou nenhum argumento CLI foi dado, inicia GUI
    if args.gui or (not args.load_default and not args.bundle and not args.boot_recovery and not args.no_gui and not args.script):
        print("Iniciando interface gráfica GSCX...")
        return create_gui_with_splash()

    # Modo CLI
    loader = ModulesLoader(on_log)

    if args.bundle:
        print(f"Carregando bundle: {args.bundle}")
        loader.load_from_gscore(args.bundle)
    else:
        print("Carregando módulos dos diretórios padrão...")
        loader.load_default_modules()

    if args.boot_recovery:
        loader.boot_recovery()

    # Execução de script Lua no modo CLI
    if args.script:
        engine = ScriptingEngine(loader, on_output=lambda s: print(s, end=""))
        if not engine.available():
            print("[Scripting] Lua runtime não disponível. Instale 'lupa' (pip install lupa).")
            return 2
        try:
            engine.run_file(args.script)
        except Exception as e:
            print(f"[Scripting][Erro] {e}")
            return 1

    # Mantenha o processo vivo para operações CLI quando não há script
    if not args.script:
        print("GSCX iniciado em modo CLI. Pressione Ctrl+C para sair.")
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nEncerrando GSCX...")
            return 0
    return 0

if __name__ == "__main__":
    raise SystemExit(main())