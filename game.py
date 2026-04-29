"""
game.py — Tavla oyun motoru.

Tüm kural mantığı burada; UI ve ağ katmanından tamamen bağımsız.
Python 3.8+ uyumlu.
"""

from __future__ import annotations   # str | None syntax için Python 3.8/3.9'da gerekli
import random
import copy

# ──────────────────────────────────────────────
# Sabitler
# ──────────────────────────────────────────────
BOARD_SIZE   = 24
MAX_PIECES   = 15
WHITE_HOME   = range(18, 24)   # white'ın evi: 18-23
BLACK_HOME   = range(0, 6)     # black'in evi: 0-5
BAR_INDEX    = -1              # bar'ı temsil eden sanal index
BEAR_OFF_IDX = 24              # bear-off'u temsil eden sanal index


# ──────────────────────────────────────────────
# Veri sınıfları
# ──────────────────────────────────────────────
class Point:
    """Tahta üzerindeki tek bir noktayı temsil eder."""

    def __init__(self, owner: str | None = None, count: int = 0):
        self.owner = owner   # "white" | "black" | None
        self.count = count

    def is_empty(self) -> bool:
        return self.count == 0

    def is_blot(self) -> bool:
        """Rakip tarafından kırılabilecek tek taş."""
        return self.count == 1

    def __repr__(self):
        return f"Point({self.owner}, {self.count})"


class Board:
    """24 nokta, bar ve bear-off alanlarını içeren tahta."""

    def __init__(self):
        self.points: list[Point] = [Point() for _ in range(BOARD_SIZE)]
        self.bar:      dict[str, int] = {"white": 0, "black": 0}
        self.bear_off: dict[str, int] = {"white": 0, "black": 0}
        self._setup()

    def _setup(self):
        """Başlangıç taş dizilimini yerleştirir."""
        # White taşları
        self.points[0]  = Point("white", 2)
        self.points[11] = Point("white", 5)
        self.points[16] = Point("white", 3)
        self.points[18] = Point("white", 5)
        # Black taşları
        self.points[23] = Point("black", 2)
        self.points[12] = Point("black", 5)
        self.points[7]  = Point("black", 3)
        self.points[5]  = Point("black", 5)

    def reset(self):
        self.__init__()

    def __repr__(self):
        lines = [f"{i:2d}: {p}" for i, p in enumerate(self.points)]
        lines.append(f"BAR: {self.bar}")
        lines.append(f"BEAR-OFF: {self.bear_off}")
        return "\n".join(lines)


class Dice:
    """Zar atma mantığı."""

    @staticmethod
    def roll() -> list[int]:
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        return [d1, d1, d1, d1] if d1 == d2 else [d1, d2]


# ──────────────────────────────────────────────
# Ana oyun sınıfı
# ──────────────────────────────────────────────
class Game:

    def __init__(self):
        self.board          = Board()
        self.dice           = Dice()
        self.current_player = "white"
        self.moves_left     = self.dice.roll()
        self.game_over      = False

    # ── Yardımcı sorgu fonksiyonları ──────────

    def opponent(self) -> str:
        return "black" if self.current_player == "white" else "white"

    def direction(self) -> int:
        """White +1 yönünde, black -1 yönünde hareket eder."""
        return 1 if self.current_player == "white" else -1

    def _calc_end(self, start: int, die: int) -> int:
        """Zar değerine göre hedef noktayı hesaplar."""
        if start == BAR_INDEX:
            # White bar'dan 0-5 arasına girer; black bar'dan 23-18 arasına
            return die - 1 if self.current_player == "white" else BOARD_SIZE - die
        return start + self.direction() * die

    def _all_in_home(self) -> bool:
        """
        Mevcut oyuncunun tüm taşları ev bölgesinde mi?
        Bar'daki taş da dışarıda sayılır.
        """
        if self.board.bar[self.current_player] > 0:
            return False

        if self.current_player == "white":
            # White evi: 18-23 → dışarıda (0-17) hiç white taşı olmamalı
            for i in range(0, 18):
                if self.board.points[i].owner == "white":
                    return False
        else:
            # Black evi: 0-5 → dışarıda (6-23) hiç black taşı olmamalı
            for i in range(6, BOARD_SIZE):
                if self.board.points[i].owner == "black":
                    return False
        return True

    def _get_furthest_piece(self) -> int | None:
        """
        Bear-off için 'en gerideki' taşı döndürür.
        White için evi en başından (18), black için evinin en sonundan (5) tarar.
        """
        if self.current_player == "white":
            # White +1 yönünde hareket eder, evi 18-23.
            # "En geride" = henüz en az mesafeyi almış = en küçük index (18'e en yakın).
            for i in range(18, BOARD_SIZE):
                if self.board.points[i].owner == "white":
                    return i   # ilk bulunan = en gerideki
        else:
            for i in range(5, -1, -1):         # 5'ten 0'a — en uzak önce
                if self.board.points[i].owner == "black":
                    return i
        return None

    def _can_bear_off(self, start: int, die: int) -> bool:
        """Bear-off hareketinin geçerli olup olmadığını kontrol eder."""
        if not self._all_in_home():
            return False

        if self.current_player == "white":
            distance = BOARD_SIZE - start       # 24 - start
            if die == distance:
                return True
            if die > distance:
                # Büyük zar → sadece en gerideki taş oynayabilir
                return start == self._get_furthest_piece()
        else:
            distance = start + 1                # 0-tabanlı mesafe
            if die == distance:
                return True
            if die > distance:
                return start == self._get_furthest_piece()

        return False

    # ── Hamle geçerlilik kontrolü ─────────────

    def _is_valid_move(self, start: int, die: int) -> bool:
        """(start, die) ikilisinin mevcut durumda geçerli olup olmadığını döndürür."""
        if die not in self.moves_left:
            return False

        # Not: Bar'da taş olsa bile kullanıcı istediği taşı oynayabilir.
        # (Standart tavla kuralı dışı - kullanıcı tercihi)

        # Kaynak kontrolü
        if start == BAR_INDEX:
            if self.board.bar[self.current_player] == 0:
                return False
        else:
            if not (0 <= start < BOARD_SIZE):
                return False
            src = self.board.points[start]
            if src.owner != self.current_player or src.is_empty():
                return False

        end = self._calc_end(start, die)

        # Bear-off durumu
        if (self.current_player == "white" and end >= BOARD_SIZE) or \
           (self.current_player == "black" and end < 0):
            return self._can_bear_off(start, die)

        # Normal hamle: hedef geçerli bir nokta olmalı
        if not (0 <= end < BOARD_SIZE):
            return False

        dst = self.board.points[end]
        # Rakibin 2+ taşı varsa gidilemez
        if dst.owner == self.opponent() and dst.count > 1:
            return False

        return True

    # ── Hamle uygulama ────────────────────────

    def _remove_from_source(self, start: int):
        """Başlangıç noktasından (veya bar'dan) bir taş kaldırır."""
        if start == BAR_INDEX:
            self.board.bar[self.current_player] -= 1
        else:
            src = self.board.points[start]
            src.count -= 1
            if src.count == 0:
                src.owner = None

    def _apply_to_destination(self, end: int) -> bool:
        """
        Hedef noktaya taş koyar; gerekirse rakibi bar'a gönderir.
        Bear-off durumunda (end dışı) direkt bear_off sayacını artırır.
        """
        # Bear-off
        if end >= BOARD_SIZE or end < 0:
            self.board.bear_off[self.current_player] += 1
            return True

        dst = self.board.points[end]

        if dst.owner is None:
            dst.owner = self.current_player
            dst.count = 1
        elif dst.owner == self.current_player:
            dst.count += 1
        else:
            # Rakip blot → bar'a gönder
            if dst.count != 1:
                return False   # 2+ taş: geçersiz (normalde buraya gelmemeli)
            self.board.bar[dst.owner] += 1
            dst.owner = self.current_player
            dst.count = 1

        return True

    def _execute_move(self, start: int, die: int) -> bool:
        end = self._calc_end(start, die)
        self._remove_from_source(start)
        return self._apply_to_destination(end)

    # ── Zar yönetimi ──────────────────────────

    def _consume_die(self, die: int):
        self.moves_left.remove(die)

    def _filter_moves_left(self):
        """
        Hiçbir zar oynanamıyorsa moves_left'i boşaltmaz (switch_turn halleder).
        Bu fonksiyon artık sadece oynanamamış zarları temizlemek için değil,
        has_any_valid_move kontrolü için kullanılır.
        """
        pass   # Büyük zar zorunluluğu kaldırıldı — kullanıcı istediği zarla oynar

    def _has_move_for_die(self, die: int) -> bool:
        """Verilen zar değeri için en az bir geçerli hamle var mı?"""
        sources = [BAR_INDEX] if self.board.bar[self.current_player] > 0 \
                  else range(BOARD_SIZE)
        for s in sources:
            if self._is_valid_move(s, die):
                return True
        return False

    # ── Genel sorgular ────────────────────────

    def get_valid_moves(self) -> list[tuple[int, int, int]]:
            """
            Mevcut durum için tüm (start, end, die) üçlülerini döndürür.
            Barda taş olsa bile kullanıcının diğer taşlarla oynamasına izin verir.
            """
            moves: list[tuple[int, int, int]] = []

            # 1. Bar'daki taşlar için hamleleri kontrol et
            if self.board.bar[self.current_player] > 0:
                for die in set(self.moves_left):
                    if self._is_valid_move(BAR_INDEX, die):
                        end = self._calc_end(BAR_INDEX, die)
                        moves.append((BAR_INDEX, end, die))

            # 2. Tahtadaki (0-23 arası) tüm taşlar için hamleleri kontrol et
            for start in range(BOARD_SIZE):
                for die in set(self.moves_left):
                    if self._is_valid_move(start, die):
                        end = self._calc_end(start, die)
                        moves.append((start, end, die))

            return moves
    def has_any_valid_move(self) -> bool:
        return bool(self.get_valid_moves())

    def check_winner(self) -> str | None:
        if self.board.bear_off["white"] == MAX_PIECES:
            return "white"
        if self.board.bear_off["black"] == MAX_PIECES:
            return "black"
        return None

    # ── Ana hamle fonksiyonu ──────────────────

    def move(self, start: int, die: int) -> bool:
        """
        (start, die) hamlesini uygular.
        Başarılıysa True, geçersizse False döndürür.
        Tüm zarlar bitince veya hamle kalmayınca sırayı değiştirir.
        """
        if self.game_over:
            return False

        if not self._is_valid_move(start, die):
            return False

        self._execute_move(start, die)
        self._consume_die(die)

        # Kazanan kontrolü
        winner = self.check_winner()
        if winner:
            self.game_over = True
            return True

        # Kalan zarlar için filtre uygula
        if self.moves_left:
            self._filter_moves_left()

        # Zarlar bitti ya da hiç hamle kalmadı → sıra değiştir
        if not self.moves_left or not self.has_any_valid_move():
            self.switch_turn()

        return True

    def switch_turn(self):
        """Sırayı rakibe geçirir ve yeni zar atar."""
        self.current_player = self.opponent()
        self.moves_left     = self.dice.roll()

        # Yeni oyuncunun da hamlesi yoksa tekrar geç
        self._filter_moves_left()
        if not self.has_any_valid_move():
            self.current_player = self.opponent()
            self.moves_left     = self.dice.roll()

    def reset(self):
        """Oyunu sıfırlar."""
        self.__init__()

    def clone(self) -> "Game":
        """Oyunun derin kopyasını döndürür (AI veya test için)."""
        return copy.deepcopy(self)