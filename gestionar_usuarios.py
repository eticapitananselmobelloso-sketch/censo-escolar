import sqlite3
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, 
                             QLineEdit, QPushButton, QLabel, QMessageBox, 
                             QInputDialog, QHeaderView)
from PyQt6.QtCore import Qt

class VentanaGestionUsuarios(QDialog):
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self.setWindowTitle("Gestión de Usuarios - Admin")
        self.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Usuario", "Contraseña"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.in_u = QLineEdit(); self.in_u.setPlaceholderText("Nombre Usuario")
        self.in_p = QLineEdit(); self.in_p.setPlaceholderText("Nueva Contraseña")
        
        btn_save = QPushButton("Guardar / Modificar")
        btn_save.clicked.connect(self.guardar_usuario)
        btn_del = QPushButton("Eliminar Seleccionado")
        btn_del.clicked.connect(self.eliminar_usuario)
        
        layout.addWidget(QLabel("<b>Usuarios del Sistema</b>"))
        layout.addWidget(self.table)
        layout.addWidget(self.in_u)
        layout.addWidget(self.in_p)
        layout.addWidget(btn_save)
        layout.addWidget(btn_del)
        
        self.cargar_usuarios()

    def cargar_usuarios(self):
        conn = sqlite3.connect(self.db_path)
        data = conn.execute("SELECT usuario, password FROM usuarios").fetchall()
        conn.close()
        self.table.setRowCount(len(data))
        for i, row in enumerate(data):
            self.table.setItem(i, 0, QTableWidgetItem(row[0]))
            self.table.setItem(i, 1, QTableWidgetItem(row[1]))

    def verificar_admin(self):
        text, ok = QInputDialog.getText(self, "Acceso Admin", "Clave Master:", QLineEdit.EchoMode.Password)
        return ok and text == "admin"

    def guardar_usuario(self):
        if self.verificar_admin():
            conn = sqlite3.connect(self.db_path)
            conn.execute("INSERT OR REPLACE INTO usuarios (usuario, password) VALUES (?, ?)", (self.in_u.text(), self.in_p.text()))
            conn.commit(); conn.close(); self.cargar_usuarios()
        else: QMessageBox.warning(self, "Error", "Clave incorrecta")

    def eliminar_usuario(self):
        if self.verificar_admin():
            sel = self.table.currentItem()
            if sel:
                u = self.table.item(sel.row(), 0).text()
                conn = sqlite3.connect(self.db_path)
                conn.execute("DELETE FROM usuarios WHERE usuario=?", (u,))
                conn.commit(); conn.close(); self.cargar_usuarios()
        else: QMessageBox.warning(self, "Error", "Clave incorrecta")
