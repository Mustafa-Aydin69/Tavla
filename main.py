from PySide6.QtWidgets import QMainWindow, QApplication, QMessageBox, QLabel
from PySide6.QtCore import Qt
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

        self.statusLabel = QLabel("Oyun bekleniyor...")
        self.statusLabel.setStyleSheet("font-size: 16px; font-weight: bold; color: #333; padding: 5px;")
        self.statusLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.ui.horizontalLayout_2.addWidget(self.statusLabel)

        self.barLabel = QLabel("BAR\nBoş")
        self.barLabel.setStyleSheet("font-size: 14px; font-weight: bold; color: #555; border: 2px dashed #999; padding: 5px;")
        self.ui.horizontalLayout_2.addWidget(self.barLabel)

        self.bearOffLabel = QLabel("Henüz çıkan taş yok")
        self.bearOffLabel.setStyleSheet("font-size: 14px; font-weight: bold; color: #555; border: 2px dashed #999; padding: 5px;")
        self.ui.horizontalLayout_2.addWidget(self.bearOffLabel)

        self.valid_starts = set()
        self.selected_start = None
        self.valid_moves = []
        self.bar_active = False

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
            self.statusLabel.setText("Rakip bekleniyor...")

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
                print("STATE geldi, UI resetlendi")
                self.reset_ui()
                self.update_turn(state)
                self.update_dice(state)
                self.update_valid_moves(state)
                self.update_board(state)
                self.update_status(state)
                self.update_bar(state)
                self.update_bear_off(state)

        # Gelen diğer mesajları takip edebilmek için debug logu bırakıyoruz
        # print("UI aldı:", msg)

    def reset_ui(self):
        self.selected_start = None
        self.bar_active = False
        
        for i in range(24):
            if i < len(self.points):
                self.points[i].setStyleSheet("")

    def update_turn(self, state):
        current_player = state.get("current_player")
        if current_player:
            text = "Beyaz" if current_player == "white" else "Siyah"
            self.ui.Turn_Status.setText(text)

    def update_dice(self, state):
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

    def update_valid_moves(self, state):
        valid_moves = state.get("valid_moves", [])
        self.valid_moves = valid_moves
        
        self.valid_starts = set(m[0] for m in valid_moves)
        self.selected_start = None
        self.bar_active = -1 in self.valid_starts

    def update_board(self, state):
        points = state.get("points", [])
        for i in range(24):
            btn = self.points[i]
            bg_color = "yellow" if i in self.valid_starts else "transparent"
            
            if i < len(points):
                owner = points[i].get("owner")
                count = points[i].get("count")
                
                if count > 0:
                    owner_tr = "Byz" if owner == "white" else "Syh"
                    # Taşı göster
                    btn.setText(f"{i}\n{owner_tr}\n({count})")
                    if owner == "white":
                        btn.setStyleSheet(f"background-color: {bg_color}; color: #555; border: 2px solid white; font-weight: bold;")
                    else:
                        btn.setStyleSheet(f"background-color: {bg_color}; color: black; border: 2px solid black; font-weight: bold;")
                else:
                    btn.setText(str(i))
                    btn.setStyleSheet(f"background-color: {bg_color}; color: black; font-weight: bold;")
            else:
                btn.setText(str(i))
                btn.setStyleSheet(f"background-color: {bg_color}; color: black; font-weight: bold;")

    def update_status(self, state):
        current_player = state.get("current_player")
        moves_left = state.get("moves_left", [])
        valid_moves = state.get("valid_moves", [])

        if current_player != self.my_color:
            self.statusLabel.setText("Rakip oynuyor")
        elif not moves_left:
            self.statusLabel.setText("Zar at")
        elif not valid_moves:
            self.statusLabel.setText("Hamle yok")
        elif -1 in self.valid_starts:
            self.statusLabel.setText("Önce kırılan taşı gir")
        else:
            self.statusLabel.setText("Hamle yap")

    def update_bar(self, state):
        bar = state.get("bar", {})
        black_bar = bar.get("black", 0)
        white_bar = bar.get("white", 0)

        if black_bar == 0 and white_bar == 0:
            self.barLabel.setText("BAR\nBoş")
            self.barLabel.setStyleSheet("font-size: 14px; font-weight: bold; color: #555; border: 2px dashed #999; padding: 5px;")
        else:
            self.barLabel.setText(f"BAR\nBeyaz: {white_bar}\nSiyah: {black_bar}")
            self.barLabel.setStyleSheet("font-size: 14px; font-weight: bold; color: darkred; border: 2px solid darkred; padding: 5px;")

    def update_bear_off(self, state):
        bear_off = state.get("bear_off", {})
        black_off = bear_off.get("black", 0)
        white_off = bear_off.get("white", 0)

        if black_off == 0 and white_off == 0:
            self.bearOffLabel.setText("Henüz çıkan taş yok")
            self.bearOffLabel.setStyleSheet("font-size: 14px; font-weight: bold; color: #555; border: 2px dashed #999; padding: 5px;")
        else:
            self.bearOffLabel.setText(f"Çıkan Taşlar\nBeyaz: {white_off}\nSiyah: {black_off}")
            self.bearOffLabel.setStyleSheet("font-size: 14px; font-weight: bold; color: darkgreen; border: 2px solid darkgreen; padding: 5px;")

    def on_point_clicked(self, index):
        if self.bar_active:
            selected_move = None
            for move in self.valid_moves:
                if move[0] == -1 and move[1] == index:
                    selected_move = move
                    break
            
            if selected_move:
                die = selected_move[2]
                if self.client:
                    self.client.send({
                        "type": "MOVE",
                        "moves": [(-1, die)]
                    })
                
                self.bar_active = False
                for i in range(24):
                    self.points[i].setStyleSheet("")
                return
            else:
                self.statusLabel.setText("Geçersiz seçim")
                return

        if self.selected_start is not None:
            # Hedef kontrolü
            selected_move = None
            for move in self.valid_moves:
                if move[0] == self.selected_start and move[1] == index:
                    selected_move = move
                    break
            
            if selected_move:
                # Doğru hedef, hamleyi gönder
                die = selected_move[2]
                if self.client:
                    self.client.send({
                        "type": "MOVE",
                        "moves": [(self.selected_start, die)]
                    })
                
                self.selected_start = None
                # Gönderdikten sonra highlight'ları temizle
                for i in range(24):
                    self.points[i].setStyleSheet("")
                return
            
            # Eğer hedefe tıklamadıysa, belki başka bir başlangıç taşı seçmiştir
            if index in self.valid_starts:
                self.selected_start = index
            else:
                self.statusLabel.setText("Geçersiz seçim")
                return  # İlgisiz tıklama
        else:
            # Henüz başlangıç seçilmediyse
            if index not in self.valid_starts:
                self.statusLabel.setText("Geçersiz seçim")
                return
            self.selected_start = index

        # Bu taş için gidebileceği hedefleri bul
        targets = [move[1] for move in self.valid_moves if move[0] == self.selected_start]

        # Buton renklerini güncelle
        for i in range(24):
            if i == self.selected_start:
                # Seçilen taş
                self.points[i].setStyleSheet("background-color: lightgreen; color: black; font-weight: bold;")
            elif i in targets:
                # Gidebileceği hedefler
                self.points[i].setStyleSheet("background-color: lightblue; color: black; font-weight: bold;")
            elif i in self.valid_starts:
                # Diğer oynanabilir taşlar
                self.points[i].setStyleSheet("background-color: yellow; color: black; font-weight: bold;")
            else:
                # Diğer boş veya oynanamaz taşlar
                self.points[i].setStyleSheet("")

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
