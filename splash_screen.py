import sys
import os
from PyQt6.QtWidgets import QSplashScreen, QProgressBar
from PyQt6.QtCore import Qt, QTimer, QRect, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPixmap, QColor, QPainter, QFont

class SplashScreen(QSplashScreen):
    def __init__(self):
        ancho, alto = 450, 500
        fondo = QPixmap(ancho, alto)
        fondo.fill(QColor("#FFFFFF"))
        
        super().__init__(fondo)
        
        painter = QPainter(fondo)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 1. Título y Logo
        painter.setPen(QColor("#333333"))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(QRect(0, 20, ancho, 30), Qt.AlignmentFlag.AlignCenter, "BIENVENIDO AL SISTEMA")
        
        if os.path.exists("logo.jpg"):
            logo = QPixmap("logo.jpg").scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            painter.drawPixmap((ancho - logo.width()) // 2, 60, logo)
            
        painter.setPen(QColor("#1e3a8a"))
        painter.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        painter.drawText(QRect(0, 260, ancho, 50), Qt.AlignmentFlag.AlignCenter, "E.T.I. Capitán Anselmo Belloso")
        
        painter.end()
        self.setPixmap(fondo)
        
        # 2. Barra de Progreso con BORDES RECTOS
        self.progreso = QProgressBar(self)
        self.progreso.setGeometry(60, 410, 330, 25)
        
        # Eliminamos el border-radius para que sea totalmente rectangular
        self.progreso.setStyleSheet("""
            QProgressBar {
                border: 1px solid #C5A059;
                background-color: #FDFBF7;
                border-radius: 0px; 
                color: #5D4037;
                font-weight: bold;
                font-size: 11px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                            stop:0 #D4AF37, stop:0.5 #F4E071, stop:1 #D4AF37);
                border-radius: 0px;
                margin: 0px;
            }
        """)
        self.progreso.setRange(0, 100)
        self.progreso.setFormat("Sincronizando... %p%")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

    def iniciar_y_cerrar(self, ventana_siguiente):
        self.show()
        
        # Animación de 3 segundos
        self.animacion = QPropertyAnimation(self.progreso, b"value")
        self.animacion.setDuration(3000)
        self.animacion.setStartValue(0)
        self.animacion.setEndValue(100)
        self.animacion.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animacion.start()
        
        QTimer.singleShot(3000, lambda: [self.close(), ventana_siguiente.show()])
