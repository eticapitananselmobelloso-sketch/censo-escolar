from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
from PyQt6.QtCore import Qt
import sqlite3

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Acceso - Sistema E.T.I. Capitán Anselmo Belloso")
        self.setFixedSize(300, 200)
        
        layout = QVBoxLayout()
        
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Usuario")
        
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Contraseña")
        self.pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        btn_login = QPushButton("Ingresar")
        btn_login.clicked.connect(self.verificar_login)
        
        layout.addWidget(QLabel("Ingrese sus credenciales:"))
        layout.addWidget(self.user_input)
        layout.addWidget(self.pass_input)
        layout.addWidget(btn_login)
        self.setLayout(layout)

    def verificar_login(self):
        user = self.user_input.text()
        pwd = self.pass_input.text()
        
        conn = sqlite3.connect('censo_belloso.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE usuario=? AND password=?", (user, pwd))
        if cursor.fetchone():
            self.accept() # Cierra el login y permite seguir al programa
        else:
            QMessageBox.warning(self, "Error", "Usuario o contraseña incorrectos")
        conn.close()
