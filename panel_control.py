import sys
import sqlite3
import os
import subprocess
import pandas as pd
from datetime import datetime

# PyQt6 imports
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QPushButton, 
                             QTableWidget, QTableWidgetItem, QWidget, QMessageBox, 
                             QHBoxLayout, QLabel, QLineEdit, QSplitter, QFrame, QSizePolicy)
from PyQt6.QtGui import QPixmap, QPainter, QPainterPath
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from login import LoginWindow
# --- NUEVA IMPORTACIÓN ---
from gestionar_usuarios import VentanaGestionUsuarios

# --- IMPORTACIÓN DE LÓGICA ---
try:
    from procesar_censo import procesar
except ImportError:
    def procesar(): pass

class WorkerThread(QThread):
    finished = pyqtSignal()
    def run(self):
        procesar()
        self.finished.emit()

# --- CSS PROFESIONAL ---
ESTILO_CSS = """
    QWidget { font-family: 'Segoe UI', sans-serif; background-color: #2c3e50; color: #ecf0f1; }
    QFrame#sidebar { background-color: #1a252f; border-right: 2px solid #34495e; }
    QPushButton { 
        background-color: #34495e; color: #ffffff; padding: 12px; border: none; 
        border-radius: 8px; font-weight: bold; margin: 5px; text-align: left; 
    }
    QPushButton:hover { background-color: #3498db; }
    QTableWidget { background-color: #ffffff; color: #2c3e50; border-radius: 8px; }
    QHeaderView::section { background-color: #34495e; color: white; padding: 5px; font-weight: bold; }
    QLineEdit { padding: 8px; border-radius: 5px; border: 1px solid #3498db; background-color: #ffffff; color: #2c3e50; }
    
    QLabel#titulo { font-size: 20px; font-weight: bold; color: #ecf0f1; background: transparent; border: none; padding: 0; margin: 0; }
    QLabel#hora { font-size: 14px; color: #bdc3c7; background: transparent; border: none; padding: 0; margin: 0; }
"""

class PanelControl(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema de Gestión - E.T.I. Capitán Anselmo Belloso")
        self.setGeometry(100, 100, 1250, 750)
        self.setStyleSheet(ESTILO_CSS)
        
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = os.path.join(self.base_dir, 'censo_belloso.db')
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        # Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(sidebar)
        
        self.logo_lbl = QLabel()
        self.logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = os.path.join(self.base_dir, "logo.jpg")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_lbl.setPixmap(self.mask_circle(pix, 120))
        sidebar_layout.addWidget(self.logo_lbl)

        # Botones (Agregado Gestión Usuarios)
        btns = [("🏠 Panel Principal", lambda: None), 
                ("🚀 Procesar Sincronización", self.ejecutar_proceso), 
                ("⚙️ Gestión Usuarios", self.abrir_gestion_usuarios),
                ("🪪 Gestión de Carnets", lambda: QMessageBox.information(self, "Carnets", "Módulo en desarrollo.")),
                ("📁 Carpeta Adjuntos", lambda: self.abrir_carpeta(os.path.join(self.base_dir, "adjuntos_censo"))),
                ("📂 Carpeta Exportados", lambda: self.abrir_carpeta(os.path.join(self.base_dir, "exportaciones_censo"))),
                ("📊 Exportar CSV", self.exportar)]
        
        for t, f in btns:
            b = QPushButton(t)
            b.clicked.connect(f)
            sidebar_layout.addWidget(b)
        sidebar_layout.addStretch()
        main_layout.addWidget(sidebar)

        # Área de trabajo
        work_area = QVBoxLayout()
        work_area.setSpacing(10)
        
        header_container = QWidget()
        header_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(0, 0, 0, 5)
        
        lbl_titulo = QLabel("Base de Datos - Aspirantes")
        lbl_titulo.setObjectName("titulo")
        self.lbl_hora = QLabel()
        self.lbl_hora.setObjectName("hora")
        
        header_layout.addWidget(lbl_titulo)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_hora)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.actualizar_hora)
        self.timer.start(1000)
        self.actualizar_hora()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar en todos los campos...")
        self.search_input.textChanged.connect(self.filtrar_tabla)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.table = QTableWidget()
        self.table.itemSelectionChanged.connect(self.mostrar_fotos)
        self.table.itemChanged.connect(self.guardar_edicion)
        
        self.foto_panel = QWidget()
        self.foto_panel.setFixedWidth(220)
        foto_vbox = QVBoxLayout(self.foto_panel)
        self.lbl_foto_rep = QLabel("Seleccione fila")
        self.lbl_foto_alum = QLabel("Seleccione fila")
        foto_vbox.addWidget(QLabel("Representante:")); foto_vbox.addWidget(self.lbl_foto_rep)
        foto_vbox.addWidget(QLabel("Alumno:")); foto_vbox.addWidget(self.lbl_foto_alum); foto_vbox.addStretch()
        
        splitter.addWidget(self.table)
        splitter.addWidget(self.foto_panel)
        
        work_area.addWidget(header_container)
        work_area.addWidget(self.search_input)
        work_area.addWidget(splitter)
        main_layout.addLayout(work_area)
        
        self.actualizar_tabla()

    # --- NUEVA FUNCIÓN PARA ABRIR VENTANA ---
    def abrir_gestion_usuarios(self):
        ventana = VentanaGestionUsuarios(self.db_path)
        ventana.exec()

    def mask_circle(self, pixmap, size):
        target = QPixmap(size, size); target.fill(Qt.GlobalColor.transparent)
        p = QPainter(target); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        path = QPainterPath(); path.addEllipse(0, 0, size, size); p.setClipPath(path)
        p.drawPixmap(0, 0, pixmap); p.end(); return target

    def actualizar_hora(self): 
        self.lbl_hora.setText(datetime.now().strftime("%d/%m/%Y - %I:%M:%S %p"))

    def guardar_edicion(self, item):
        try:
            f, c = item.row(), item.column()
            col = self.table.horizontalHeaderItem(c).text()
            idx = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())].index('cedula_alumno')
            cedula = self.table.item(f, idx).text()
            with sqlite3.connect(self.db_path) as conn: 
                conn.execute(f"UPDATE aspirantes SET {col} = ? WHERE cedula_alumno = ?", (item.text(), cedula))
        except Exception as e:
            print(f"Error guardando edición: {e}")

    def mostrar_fotos(self):
        sel = self.table.selectedItems()
        if not sel: return
        try:
            row = sel[0].row()
            header = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
            r1 = self.table.item(row, header.index('foto_rep_url')).text()
            r2 = self.table.item(row, header.index('foto_alumno_url')).text()
            for lbl, r in [(self.lbl_foto_rep, r1), (self.lbl_foto_alum, r2)]:
                ruta_completa = os.path.join(self.base_dir, r)
                if os.path.exists(ruta_completa): 
                    lbl.setPixmap(QPixmap(ruta_completa).scaled(150, 150, Qt.AspectRatioMode.KeepAspectRatio))
                else: 
                    lbl.setText("No disponible")
        except Exception as e:
            print(f"Error mostrando fotos: {e}")

    def actualizar_tabla(self, query="SELECT * FROM aspirantes"):
        try:
            conn = sqlite3.connect(self.db_path)
            df = pd.read_sql_query(query, conn)
            conn.close()
            self.table.blockSignals(True)
            self.table.setRowCount(len(df))
            self.table.setColumnCount(len(df.columns))
            self.table.setHorizontalHeaderLabels(df.columns)
            for i in range(len(df)):
                for j in range(len(df.columns)):
                    self.table.setItem(i, j, QTableWidgetItem(str(df.iloc[i, j])))
            self.table.blockSignals(False)
        except Exception as e:
            print(f"Error actualizando tabla: {e}")

    def filtrar_tabla(self):
        text = self.search_input.text()
        cols = ['cedula_alumno', 'nombre_alumno', 'nombre_rep', 'correo_rep', 'cedula_rep']
        query = f"SELECT * FROM aspirantes WHERE " + " OR ".join([f"{col} LIKE '%{text}%'" for col in cols])
        self.actualizar_tabla(query)

    def exportar(self):
        try:
            export_dir = os.path.join(self.base_dir, "exportaciones_censo")
            if not os.path.exists(export_dir): 
                os.makedirs(export_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            ruta_csv = os.path.join(export_dir, f"reporte_{timestamp}.csv")
            with sqlite3.connect(self.db_path) as conn: 
                df = pd.read_sql_query("SELECT * FROM aspirantes", conn)
            df.to_csv(ruta_csv, index=False, sep=';', encoding='utf-8-sig')
            QMessageBox.information(self, "Exportación Exitosa", f"El archivo fue guardado en:\n{ruta_csv}")
        except Exception as e: 
            QMessageBox.critical(self, "Error Crítico", f"Falló la exportación:\n{str(e)}")

    def ejecutar_proceso(self):
        QMessageBox.information(self, "Procesando", "Sincronizando...")
        self.worker = WorkerThread()
        self.worker.finished.connect(lambda: [self.actualizar_tabla(), QMessageBox.information(self, "Finalizado", "Sincronización concluida.")])
        self.worker.start()

    def abrir_carpeta(self, ruta_carpeta): 
        try:
            if not os.path.exists(ruta_carpeta): 
                os.makedirs(ruta_carpeta, exist_ok=True)
            subprocess.Popen(['xdg-open', ruta_carpeta])
        except Exception as e:
            QMessageBox.warning(self, "Error al abrir", f"No se pudo abrir la carpeta:\n{str(e)}")

# --- IMPORTACIONES NECESARIAS ---
from splash_screen import SplashScreen

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 1. Instanciamos los objetos
    # Asegúrate de haber importado SplashScreen desde splash_screen.py
    splash = SplashScreen()
    login = LoginWindow()
    
    # 2. Iniciamos el Splash (el cual se encarga de la barra y el tiempo de 3s)
    # Le pasamos el login como ventana a abrir al finalizar
    splash.iniciar_y_cerrar(login)
    
    # 3. Lógica de transición tras el Login
    def abrir_panel_principal():
        # Esta función se ejecutará solo cuando el login sea exitoso
        global ventana_principal # Opcional: mantiene la referencia en memoria
        ventana_principal = PanelControl()
        ventana_principal.show()
    
    # Conectamos la señal 'accepted' del login con nuestra función
    login.accepted.connect(abrir_panel_principal)
    
    # 4. Ejecutamos el bucle de la aplicación
    sys.exit(app.exec())
 
