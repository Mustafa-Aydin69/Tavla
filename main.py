from PySide6.QtWidgets import QMainWindow, QApplication, QMessageBox
from game_ui import Ui_Oyun_Tahtasi
import sys
from client.client import GameClient
from signal_bridge import SignalBridge

print(sys.executable)


class GameWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_Oyun_Tahtasi()
        self.ui.setupUi(self)

        # direkt erişim
        self.boardContainer = self.ui.boardContainer

        self.init_board()

        self.client = GameClient()
        self.bridge = SignalBridge()

        self.client.on_message = lambda msg: self.bridge.message.emit(msg)
        self.bridge.message.connect(self.handle_server_message)

        self.client.start()

    def handle_server_message(self, msg):
        msg_type = msg.get("type")

        if msg_type == "WAITING":
            self.ui.player_status.setText("Rakip bekleniyor...")

        elif msg_type == "MATCH":
            color = msg.get("color")
            # Türkçeleştirme
            if color == "white":
                display_color = "Beyaz"
            elif color == "black":
                display_color = "Siyah"
            else:
                display_color = color

            self.ui.player_status.setText(f"Renginiz: {display_color}")

        elif msg_type == "OPPONENT_DISCONNECTED":
            reply = QMessageBox.question(
                self, 
                "Oyun Bitti", 
                "Rakip oyundan ayrıldı. Kazandınız!\nTekrar oynamak ister misiniz?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.client.stop()
                self.client = GameClient()
                self.client.on_message = lambda m: self.bridge.message.emit(m)
                self.client.start()
            else:
                self.client.stop()
                QApplication.quit()

        # Gelen diğer mesajları takip edebilmek için debug logu bırakıyoruz
        print("UI aldı:", msg)

    def init_board(self):
        from PySide6.QtWidgets import QPushButton, QGridLayout

        layout = QGridLayout()
        self.boardContainer.setLayout(layout)

        self.points = []

        for i in range(24):
            btn = QPushButton(str(i))
            btn.setFixedSize(60, 100)

            row = 0 if i < 12 else 1
            col = i if i < 12 else 23 - i

            layout.addWidget(btn, row, col)
            self.points.append(btn)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GameWindow()
    window.show()
    sys.exit(app.exec())
