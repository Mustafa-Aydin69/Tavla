from PySide6.QtWidgets import QMainWindow, QApplication, QMessageBox, QLabel
from game_ui import Ui_Oyun_Tahtasi
import sys
from client.client import GameClient
from signal_bridge import SignalBridge

print(sys.executable)


class GameWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.my_color = None
        self.ui = Ui_Oyun_Tahtasi()
        self.ui.setupUi(self)

        # direkt erişim
        self.boardContainer = self.ui.boardContainer

        self.init_board()

        self.validMovesLabel = QLabel("Geçerli hamleler bekleniyor...")
        self.validMovesLabel.setStyleSheet("font-size: 14px; font-weight: bold; color: #333;")
        self.ui.horizontalLayout_2.addWidget(self.validMovesLabel)

        self.valid_starts = set()
        self.selected_start = None

        self.client = GameClient()
        self.bridge = SignalBridge()

        self.client.on_message = lambda msg: self.bridge.message.emit(msg)
        self.bridge.message.connect(self.handle_server_message)

        self.ui.dice_Button.clicked.connect(self.request_roll)

        self.client.start()

    def request_roll(self):
        if self.client:
            self.client.send({"type": "ROLL"})

    def handle_server_message(self, msg):
        msg_type = msg.get("type")

        if msg_type == "WAITING":
            self.ui.player_status.setText("Rakip bekleniyor...")

        elif msg_type == "MATCH":
            color = msg.get("color")
            self.my_color = color
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

        elif msg_type == "STATE":
            state = msg.get("state")
            if state is not None:
                dice = state.get("moves_left", [])
                current_player = state.get("current_player")

                # Buton kontrolü
                if current_player and self.my_color and current_player == self.my_color and len(dice) == 0:
                    self.ui.dice_Button.setEnabled(True)
                else:
                    self.ui.dice_Button.setEnabled(False)

                # Zar metinlerini güncelle
                if len(dice) == 0:
                    self.ui.Zar_lcdNumber_lcdNumber_2.setText("-")
                    self.ui.dice_lcdNumber.setText("-")
                elif len(dice) == 1:
                    self.ui.Zar_lcdNumber_lcdNumber_2.setText(str(dice[0]))
                    self.ui.dice_lcdNumber.setText("")
                elif len(dice) == 2:
                    self.ui.Zar_lcdNumber_lcdNumber_2.setText(str(dice[0]))
                    self.ui.dice_lcdNumber.setText(str(dice[1]))
                elif len(dice) >= 3:
                    self.ui.Zar_lcdNumber_lcdNumber_2.setText(f"{dice[0]} (x{len(dice)})")
                    self.ui.dice_lcdNumber.setText("")

                # Geçerli hamleleri göster
                valid_moves = state.get("valid_moves", [])
                
                self.valid_starts = set(m[0] for m in valid_moves)
                self.selected_start = None
                
                if valid_moves:
                    moves_str = "\n".join([f"{m[0]} → {m[1]}" for m in valid_moves])
                    self.validMovesLabel.setText(f"Geçerli hamleler:\n{moves_str}")
                else:
                    self.validMovesLabel.setText("Geçerli hamle yok")

                # Butonları valid_starts'a göre renklendir
                for i in range(24):
                    if i in self.valid_starts:
                        self.points[i].setStyleSheet("background-color: yellow; color: black; font-weight: bold;")
                    else:
                        self.points[i].setStyleSheet("")

        # Gelen diğer mesajları takip edebilmek için debug logu bırakıyoruz
        print("UI aldı:", msg)

    def on_point_clicked(self, index):
        if index not in self.valid_starts:
            return

        self.selected_start = index

        # Tüm geçerli olanları sarıya geri döndür
        for i in range(24):
            if i in self.valid_starts:
                self.points[i].setStyleSheet("background-color: yellow; color: black; font-weight: bold;")
            else:
                self.points[i].setStyleSheet("")

        # Seçilen butonu yeşil yap
        if 0 <= index <= 23:
            self.points[index].setStyleSheet("background-color: lightgreen; color: black; font-weight: bold;")

    def init_board(self):
        from PySide6.QtWidgets import QPushButton, QGridLayout

        layout = QGridLayout()
        self.boardContainer.setLayout(layout)

        self.points = []

        for i in range(24):
            btn = QPushButton(str(i))
            btn.setFixedSize(60, 100)
            btn.clicked.connect(lambda checked=False, i=i: self.on_point_clicked(i))

            row = 0 if i < 12 else 1
            col = i if i < 12 else 23 - i

            layout.addWidget(btn, row, col)
            self.points.append(btn)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GameWindow()
    window.show()
    sys.exit(app.exec())
