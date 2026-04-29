from __future__ import annotations
"""
main.py — Tavla Qt arayüzü.
Sadece görsel render ve kullanıcı etkileşimini yönetir.
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QGridLayout,
    QLabel, QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt, QRect, QPoint, QSize
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QPainter, QBrush, QPen,
    QPolygon, QPixmap, QPainterPath
)
from PyQt6.QtWidgets import QPushButton

from game_ui import Ui_Oyun_Tahtasi
from game import Game, BAR_INDEX, BOARD_SIZE

# ── Renkler ────────────────────────────────────
CLR_POINT_GREY   = QColor("#888888")   # gri üçgen
CLR_POINT_BEIGE  = QColor("#D4B896")   # bej üçgen
CLR_BOARD_BG     = QColor("#FFFFFF")   # tahta arka planı (koyu kahve)
CLR_SELECTED     = QColor("#FFD700")   # seçili (altın)
CLR_VALID        = QColor("#4FC040")   # geçerli hedef (yeşil)
CLR_WHITE_PIECE  = QColor("#F0EDE0")   # beyaz taş
CLR_BLACK_PIECE  = QColor("#1A1A1A")   # siyah taş
CLR_PIECE_BORDER = QColor("#555555")


# ──────────────────────────────────────────────
# Özel Point widget — gerçek üçgen çizer
# ──────────────────────────────────────────────
class PointWidget(QPushButton):
    """
    Bir tavla noktasını (üçgeni) temsil eden widget.
    Taşları üçgenin üzerine daireler olarak çizer.
    """

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.point_index  = index
        self.piece_owner  = None   # "white" | "black" | None
        self.piece_count  = 0
        self.highlight    = "none" # "none" | "selected" | "valid"

        # Üst sıra (0-11): aşağı bakan üçgen
        # Alt sıra (12-23): yukarı bakan üçgen
        self.is_top = index < 12

        self.setFixedSize(80, 240)
        self.setFlat(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        # Arkaplanı şeffaf yap — kendi paintEvent'i çizecek
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent; border: none;")
        
    def set_state(self, owner, count, highlight="none"):
        self.piece_owner = owner
        self.piece_count = count
        self.highlight   = highlight
        self.update()   # repaint

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()

        # ── 1. Üçgen Rengi Belirleme ──
        if self.highlight == "selected":
            tri_color = CLR_SELECTED
        elif self.highlight == "valid":
            tri_color = CLR_VALID
        else:
            col_idx = self.point_index if self.is_top else (23 - self.point_index)
            tri_color = CLR_POINT_GREY if col_idx % 2 == 0 else CLR_POINT_BEIGE

        # ── 2. Üçgeni Çiz ──
        path = QPainterPath()
        if self.is_top:
            path.moveTo(0, 0)
            path.lineTo(w, 0)
            path.lineTo(w / 2, h)
            path.closeSubpath()
        else:
            path.moveTo(w / 2, 0)
            path.lineTo(0, h)
            path.lineTo(w, h)
            path.closeSubpath()

        painter.setBrush(QBrush(tri_color))
        painter.setPen(QPen(QColor("#1a1a1a"), 1))
        painter.drawPath(path)

        # ── 3. Taşları Çiz (Senin takıldığın yer) ──
        if self.piece_count > 0:
            piece_color  = CLR_WHITE_PIECE if self.piece_owner == "white" else CLR_BLACK_PIECE
            text_color   = QColor("#222") if self.piece_owner == "white" else QColor("#eee")
            
            # Dinamik hesaplamalar
            max_h = h * 0.8
            # Taşlar arttıkça yarıçapı küçült ama 15'in altına çok düşürme (görünürlük için)
            radius = max(15, min(22, max_h / (self.piece_count * 2))) if self.piece_count > 1 else 22
            
            # Kaç taş gösterilecek? (Hepsini göstermek istersen min(self.piece_count, 15) yapabilirsin)
            shown = min(self.piece_count, 5)

            for i in range(shown):
                offset = i * (radius * 1.7) # Taşların birbirine ne kadar geçeceği (çarpan küçüldükçe iç içe geçerler)
                
                if self.is_top:
                    cx = w // 2
                    cy = radius + 5 + offset
                else:
                    cx = w // 2
                    cy = h - radius - 5 - offset

                # --- GÖLGE ÇİZİMİ ---
                painter.setBrush(QBrush(QColor(0, 0, 0, 60)))
                painter.setPen(Qt.PenStyle.NoPen)
                # Sol üst köşe: (Merkez - Yarıçap), Çap: (2 * Yarıçap)
                painter.drawEllipse(int(cx - radius + 2), int(cy - radius + 2), 
                                    int(radius * 2), int(radius * 2))

                # --- TAŞIN KENDİSİNİ ÇİZ ---
                painter.setBrush(QBrush(piece_color))
                painter.setPen(QPen(CLR_PIECE_BORDER, 1.5))
                painter.drawEllipse(int(cx - radius), int(cy - radius), 
                                    int(radius * 2), int(radius * 2))

            # ── 4. Sayı Gösterimi (5'ten fazla taş varsa) ──
            if self.piece_count > shown:
                painter.setPen(QPen(text_color))
                painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
                # Yazıyı en son taşın biraz ilerisine koy
                text_y = (radius * 2 + shown * radius * 1.7) if self.is_top else (h - shown * radius * 1.7 - radius * 3)
                painter.drawText(QRect(0, int(text_y), w, 20),
                                 Qt.AlignmentFlag.AlignHCenter,
                                 f"+{self.piece_count - shown}")

        painter.end()
# ──────────────────────────────────────────────
# Ana pencere
# ──────────────────────────────────────────────
class GameWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.ui = Ui_Oyun_Tahtasi()
        self.ui.setupUi(self)
        self.setWindowTitle("Tavla")

        self.game: Game          = Game()
        self.selected_point: int | None = None

        self.point_widgets: list[PointWidget]    = []
        self.bar_btn:       dict[str, QPushButton] = {}
        self.bear_btn:      dict[str, QPushButton] = {}
        self.dice_lcds:     list                   = []

        # Tahta arkaplanı
        self.ui.boardContainer.setStyleSheet(
            f"background-color: {CLR_BOARD_BG.name()}; border-radius: 8px;"
        )

        self._build_board()
        self._build_dice_display()
        self.ui.dice_Button.clicked.connect(self._on_roll_dice)
        self._refresh_ui()

    # ──────────────────────────────────────────
    # Board inşa
    # ──────────────────────────────────────────

    def _grid_pos(self, index: int) -> tuple[int, int]:
        """Board index → (row, col) grid pozisyonu."""
        if index < 12:
            row, col = 0, index
        else:
            row, col = 1, 23 - index
        if col >= 6:
            col += 1   # orta bar boşluğu
        return row, col

    def _build_board(self):
        layout = QGridLayout()
        layout.setSpacing(3)
        layout.setContentsMargins(8, 8, 8, 8)
        self.ui.boardContainer.setLayout(layout)

        # 24 point widget
        for i in range(BOARD_SIZE):
            w = PointWidget(i)
            w.clicked.connect(lambda _, idx=i: self._on_point_click(idx))
            row, col = self._grid_pos(i)
            layout.addWidget(w, row, col)
            self.point_widgets.append(w)

        # Orta çizgi
        sep = QLabel()
        sep.setFixedWidth(6)
        sep.setStyleSheet("background-color: #111; border-radius: 3px;")
        layout.addWidget(sep, 0, 6, 2, 1)

        # Bar butonları
        for player, row in [("white", 0), ("black", 1)]:
            btn = QPushButton()
            btn.setFixedSize(58, 120)
            btn.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            btn.setStyleSheet(self._bar_style())
            layout.addWidget(btn, row, 13)
            self.bar_btn[player] = btn
            btn.clicked.connect(lambda _, p=player: self._on_bar_click(p))

        # Bear-off butonları
        for player, row in [("white", 0), ("black", 1)]:
            btn = QPushButton()
            btn.setFixedSize(58, 120)
            btn.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            btn.setStyleSheet(self._bearoff_style())
            layout.addWidget(btn, row, 14)
            self.bear_btn[player] = btn
            btn.clicked.connect(self._on_bear_off_click)

    def _bar_style(self, highlight=False):
        bg = "#FFD700" if highlight else "#3a3a3a"
        fg = "#000"    if highlight else "#eee"
        return (f"background-color: {bg}; color: {fg}; "
                f"border: 2px solid #555; border-radius: 6px; font-weight: bold;")

    def _bearoff_style(self):
        return ("background-color: #1a4a1a; color: #8f8; "
                "border: 2px solid #3a3; border-radius: 6px; font-weight: bold;")

    def _build_dice_display(self):
        """Mevcut 2 LCD + 2 ekstra (çift zar için)."""
        from PyQt6.QtWidgets import QLCDNumber
        self.dice_lcds = [self.ui.dice_lcdNumber, self.ui.dice_lcdNumber1]
        parent_w = self.ui.dice_lcdNumber.parentWidget()
        parent_l = parent_w.layout() if parent_w else None
        for _ in range(2):
            lcd = QLCDNumber()
            lcd.setFixedSize(60, 40)
            lcd.setVisible(False)
            if parent_l:
                parent_l.addWidget(lcd)
            elif parent_w:
                lcd.setParent(parent_w)
            self.dice_lcds.append(lcd)

    # ──────────────────────────────────────────
    # UI güncelleme
    # ──────────────────────────────────────────

    def _refresh_ui(self):
        self._update_points()
        self._update_dice()
        self._update_status()

    def _highlight_for(self, index: int) -> str:
        """Verilen index için highlight durumunu döndürür."""
        if index == self.selected_point:
            return "selected"
        # Geçerli hedef mi?
        if self.selected_point is not None:
            valid = self.game.get_valid_moves()
            for s, e, die in valid:
                if s == self.selected_point and e == index:
                    return "valid"
        return "none"

    def _update_points(self):
        for i in range(BOARD_SIZE):
            p  = self.game.board.points[i]
            hl = self._highlight_for(i)
            self.point_widgets[i].set_state(p.owner, p.count, hl)

        # Bar butonları
        for player in ("white", "black"):
            n   = self.game.board.bar[player]
            sel = (self.selected_point == BAR_INDEX and
                   player == self.game.current_player)
            self.bar_btn[player].setText(
                f"BAR\n{'⬤ ' * min(n, 5)}\n{n}" if n else "BAR\n—"
            )
            self.bar_btn[player].setStyleSheet(self._bar_style(highlight=sel))

        # Bear-off
        for player in ("white", "black"):
            n = self.game.board.bear_off[player]
            lbl = "W" if player == "white" else "B"
            self.bear_btn[player].setText(f"OFF\n{lbl}: {n}")

    def _update_dice(self):
        dice = self.game.moves_left
        for i, lcd in enumerate(self.dice_lcds):
            if i < len(dice):
                lcd.display(dice[i])
                lcd.setVisible(True)
            else:
                lcd.display(0)
                lcd.setVisible(i < 2)

    def _update_status(self):
        player = self.game.current_player.upper()
        self.ui.Turn_Status.setText(player)
        clr = "white" if self.game.current_player == "white" else "#aaa"
        self.ui.Turn_Status.setStyleSheet(f"color: {clr}; font-weight: bold;")

    def _msg(self, text: str):
        self.statusBar().showMessage(text, 3000)

    # ──────────────────────────────────────────
    # Olay işleyiciler
    # ──────────────────────────────────────────

    def _on_roll_dice(self):
        if self.game.game_over:
            return
        if self.game.moves_left:
            self._msg("Zarlar zaten atıldı!")
            return
        self.game.moves_left = self.game.dice.roll()
        self._refresh_ui()
        if not self.game.has_any_valid_move():
            self._msg("Hiç hamle yok, sıra geçiyor…")
            self.game.switch_turn()
            self._refresh_ui()

    def _on_point_click(self, index: int):
            if self.game.game_over:
                return
            if not self.game.moves_left:
                self._msg("Önce zar atın!")
                return

            # 1. Durum: Seçili taşa tekrar tıklanırsa seçimi iptal et
            if self.selected_point == index:
                self.selected_point = None
                self._refresh_ui()
                return

            # 2. Durum: Henüz bir taş seçilmemişse, yeni bir taş seç
            if self.selected_point is None:
                pt = self.game.board.points[index]
                if pt.owner != self.game.current_player or pt.is_empty():
                    self._msg("Bu taş size ait değil.")
                    return
                self.selected_point = index
                self._refresh_ui()
                return

            # 3. Durum: Bir taş zaten seçili. 
            # ÖNCE: Tıklanan yer geçerli bir hamle hedefi mi diye bak!
            valid_moves = self.game.get_valid_moves()
            is_valid_target = any(s == self.selected_point and e == index for s, e, die in valid_moves)

            if is_valid_target:
                # Eğer geçerli bir hedefse, orada kendi taşımız olsa bile hamleyi uygula
                self._try_move(self.selected_point, index)
            else:
                # Eğer geçerli bir hedef DEĞİLSE ve tıkladığımız yerde kendi taşımız varsa, seçimi ona kaydır
                pt = self.game.board.points[index]
                if pt.owner == self.game.current_player and not pt.is_empty():
                    self.selected_point = index
                    self._refresh_ui()
                else:
                    self._msg("Geçersiz hamle.")
                    self.selected_point = None
                    self._refresh_ui()

    def _on_bar_click(self, player: str):
        if self.game.game_over:
            return
        if not self.game.moves_left:
            self._msg("Önce zar atın!")
            return
        if player != self.game.current_player:
            self._msg("Sıra sizde değil.")
            return
        if self.game.board.bar[player] == 0:
            self._msg("Bar boş.")
            return
        # Zaten seçiliyse iptal
        if self.selected_point == BAR_INDEX:
            self.selected_point = None
            self._refresh_ui()
            return
        self.selected_point = BAR_INDEX
        self._refresh_ui()

    def _on_bear_off_click(self):
        if self.game.game_over:
            return
        if self.selected_point is None:
            self._msg("Önce bir taş seçin.")
            return

        valid = self.game.get_valid_moves()
        for s, e, die in valid:
            if s == self.selected_point and (e >= BOARD_SIZE or e < 0):
                ok = self.game.move(s, die)
                if ok:
                    self.selected_point = None
                    self._refresh_ui()
                    self._check_winner()
                    return

        self._msg("Bu taşla şu an bear-off yapılamaz.")
        self.selected_point = None
        self._refresh_ui()

    def _try_move(self, start: int, end: int):
        """Seçili taştan hedef noktaya hamle dener."""
        valid = self.game.get_valid_moves()

        # İstediğin zarla oynayabilmek için: aynı (start→end) için tüm
        # uygun zarları bul; varsa en küçüğü kullan (kullanıcı seçemiyor,
        # zaten tek anlamlı hamle)
        matching = [(s, e, die) for s, e, die in valid if s == start and e == end]

        if matching:
            s, e, die = matching[0]
            ok = self.game.move(s, die)
            self.selected_point = None
            self._refresh_ui()
            if ok:
                self._check_winner()
            return

        # Geçerli hedef değil
        self._msg("Geçersiz hamle.")
        self.selected_point = None
        self._refresh_ui()

    def _check_winner(self):
        winner = self.game.check_winner()
        if not winner:
            return
        name = "Beyaz" if winner == "white" else "Siyah"
        reply = QMessageBox.question(
            self, "Oyun Bitti",
            f"🏆 {name} kazandı!\n\nTekrar oynamak ister misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.game = Game()
            self.selected_point = None
            self._refresh_ui()
        else:
            self.close()


# ──────────────────────────────────────────────
# Giriş noktası
# ──────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window,        QColor(38, 38, 38))
    pal.setColor(QPalette.ColorRole.WindowText,    QColor(220, 220, 220))
    pal.setColor(QPalette.ColorRole.Base,          QColor(28, 28, 28))
    pal.setColor(QPalette.ColorRole.Button,        QColor(55, 55, 55))
    pal.setColor(QPalette.ColorRole.ButtonText,    QColor(220, 220, 220))
    pal.setColor(QPalette.ColorRole.Highlight,     QColor(255, 215, 0))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(0, 0, 0))
    app.setPalette(pal)

    window = GameWindow()
    window.show()
    sys.exit(app.exec())