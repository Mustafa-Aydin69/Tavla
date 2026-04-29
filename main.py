from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QGridLayout
from game_ui import Ui_Oyun_Tahtasi
from PyQt6.QtWidgets import QLabel
from game import Game


class GameWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_Oyun_Tahtasi()
        self.ui.setupUi(self)
        self.game = Game()

        self.boardContainer = self.ui.boardContainer
        self.selected_point = None    
        self.ui.dice_Button.clicked.connect(self.roll_dice_ui)
        self.update_dice_display()
        self.init_board()
        self.update_board()

    def init_board(self):
        layout = QGridLayout()
        self.boardContainer.setLayout(layout)

        self.points = []

        # 🔥 POINTLER
        for i in range(24):
            btn = QPushButton()
            btn.setFixedSize(60, 100)

            row = 0 if i < 12 else 1

            if i < 12:
                col = i
            else:
                col = 23 - i

            # ortada boşluk
            if col >= 6:
                col += 1

            # dama renk
            if (row + col) % 2 == 0:
                btn.setStyleSheet("background-color: white; color: black;")
            else:
                btn.setStyleSheet("background-color: darkgray; color: blue;")

            layout.addWidget(btn, row, col)
            self.points.append(btn)

            btn.clicked.connect(lambda _, i=i: self.handle_click(i))

        bar = QLabel()
        bar.setStyleSheet("background-color: black;")
        bar.setFixedWidth(10)
        layout.addWidget(bar, 0, 6, 2, 1)
        
        self.bar_white = QPushButton(" - W BAR")
        self.bar_black = QPushButton("- B BAR")
        self.bar_white.setFixedSize(50, 100)
        self.bar_black.setFixedSize(50, 100)
        layout.addWidget(self.bar_white, 0, 13)
        layout.addWidget(self.bar_black, 1, 13)
        
        self.out_white = QPushButton(" out OW BAR")
        self.out_black = QPushButton(" out B BAR")
        self.out_white.setFixedSize(50, 100)
        self.out_black.setFixedSize(50, 100)
        layout.addWidget(self.out_white, 0, 14)
        layout.addWidget(self.out_black, 1, 14)
        self.bar_white.clicked.connect(lambda: self.select_bar("white"))
        self.bar_black.clicked.connect(lambda: self.select_bar("black"))
        self.out_white.clicked.connect(self.select_bear_off)
        self.out_black.clicked.connect(self.select_bear_off)
        
    def get_point_style(self, index):
        row = 0 if index < 12 else 1
        if index < 12:
            col = index
        else:
            col = 23 - index

        if col >= 6:
            col += 1

        if (row + col) % 2 == 0:
            return "background-color: white; color: black;"
        else:
            return "background-color: darkgray; color: blue;"
        
    def update_board(self):
        dice = self.game.moves_left

        for i in range(24):
            point = self.game.board.points[i]
            btn = self.points[i]

            if point.owner is None:
                btn.setText("")
            elif point.owner == "white":
                btn.setText(f"W{point.count}")
            else:
                btn.setText(f"B{point.count}")

            btn.setStyleSheet(self.get_point_style(i))
        self.ui.Turn_Status.setText(self.game.current_player.upper())
        self.bar_white.setText(f"W:{self.game.board.bar['white']}")
        self.bar_black.setText(f"B:{self.game.board.bar['black']}") 
        self.bar_white.clicked.connect(lambda: self.select_bar("white"))
        self.bar_black.clicked.connect(lambda: self.select_bar("black"))
        self.out_white.setText(f"W:{self.game.board.bear_off['white']}")
        self.out_black.setText(f"B:{self.game.board.bear_off['black']}")
                    
    def update_dice_display(self):
        dice = self.game.moves_left

        # 1. zar
        if len(dice) >= 1:
            self.ui.dice_lcdNumber.display(dice[0])
        else:
            self.ui.dice_lcdNumber.display(0)

        # 2. zar
        if len(dice) >= 2:
            self.ui.dice_lcdNumber1.display(dice[1])
        else:
            self.ui.dice_lcdNumber1.display(0)
    def roll_dice_ui(self):
        if len(self.game.moves_left) > 0:
            print("Zar zaten atıldı")
            return
        self.game.moves_left = self.game.dice.roll()
        print("Yeni zar:", self.game.moves_left)

        self.update_dice_display()
               
    def clear_highlights(self):
        for i, btn in enumerate(self.points):
            btn.setStyleSheet(self.get_point_style(i))

    def highlight_valid_targets(self, start):
        self.clear_highlights()

        # seçilen nokta
        self.points[start].setStyleSheet("background-color: yellow;border: 2px solid red;")

        valid_moves = self.game.get_valid_moves()

        for s, e, die in valid_moves:
            if s == start and 0 <= e <= 23:
                self.points[e].setStyleSheet("background-color: lightgreen; border: 2px solid blue;")

    def handle_click(self, index):
        print("Tıklandı:", index)

        if len(self.game.moves_left) == 0:
            print("Önce zar at!")
            return

        valid_moves = self.game.get_valid_moves()

        
        
        if self.selected_point is None:
            point = self.game.board.points[index]

            if point.owner != self.game.current_player or point.count == 0:
                print("Bu taş seçilemez.")
                return

            self.selected_point = index
            self.highlight_valid_targets(index)
            return

        start = self.selected_point
        end = index

        print(f"Move dene: {start} -> {end}")

        move_done = False
        for s, e, die in valid_moves:
            if s == start and (e == end or e < 0 or e > 23):
                print("Hamle yapılıyor:", s, e, die)
                self.game.move(s, die)
                move_done = True
                break

        self.selected_point = None
        self.update_board()
        self.update_dice_display()
        if start == -1:
            valid_moves = self.game.get_valid_moves()

            for s, e, die in valid_moves:
                if s == -1 and e == index:
                    print("Bar'dan giriş:", e)
                    self.game.move(-1, die)

                    self.selected_point = None
                    self.update_board()
                    self.update_dice_display()
                    return

            print("Geçersiz bar girişi")
            self.selected_point = None
            return
        if not move_done:
            print("Geçersiz hamle.")

        if not self.game.get_valid_moves() and len(self.game.moves_left) > 0:
            print("Hamle yok, tur geçiliyor")

            self.game.switch_turn()
            self.game.moves_left = []
            self.update_dice_display()
            self.update_board()
        winner = self.game.check_winner()
        if winner:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.information(self, "Oyun Bitti", f"Kazanan: {winner.upper()}")    
            self.game = Game()
            self.selected_point = None
            self.update_board()
            self.update_dice_display()
            return
    def select_bar(self, player):
        if self.game.current_player != player:
                print("Sıra sende değil")
                return
        if self.game.board.bar[player] == 0:
                print("Bar boş")
                return

        self.selected_point = -1
        self.clear_highlights()

        valid_moves = self.game.get_valid_moves()

        for s, e, die in valid_moves:
            if s == -1:
                self.points[e].setStyleSheet("background-color: orange;")

            print("Bar seçildi") 
               
    def select_bear_off(self):
        if self.selected_point is None:
            print("Önce taş seç")
            return

        valid_moves = self.game.get_valid_moves()

        for s, e, die in valid_moves:
            if s == self.selected_point and (e < 0 or e > 23):
                self.game.move(s, die)
                break

        self.selected_point = None
        self.update_board()
        self.update_dice_display()
        
        
        

app = QApplication([])
window = GameWindow()
window.show()
app.exec()