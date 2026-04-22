from PyQt6.QtWidgets import QApplication, QMainWindow
from game_ui import Ui_Oyun_Tahtasi

class GameWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Oyun_Tahtasi()
        self.ui.setupUi(self)

app = QApplication([])
window = GameWindow()
window.show()
app.exec()