import random


class Point:
    def __init__(self, owner=None, count=0):
        self.owner = owner  # "Siyah" veya "beyaz"
        self.count = count  # Nokta üzerindeki taş sayısı


class Board:
    def __init__(self):
        self.points = [Point() for _ in range(24)]

        self.bar = {"white": 0, "black": 0}

        self.bear_off = {"white": 0, "black": 0}

        self.init_board()

    # Tahtayı başlangıç durumuna getirir
    def init_board(self):
        # WHITE
        self.points[0] = Point("white", 2)
        self.points[11] = Point("white", 5)
        self.points[16] = Point("white", 3)
        self.points[18] = Point("white", 5)

        # BLACK
        self.points[23] = Point("black", 2)
        self.points[12] = Point("black", 5)
        self.points[7] = Point("black", 3)
        self.points[5] = Point("black", 5)

    def print_board(self):
        for i, p in enumerate(self.points):
            print(f"{i}: {p.owner} - {p.count}")

        print("BAR:", self.bar)
        print("BEAR OFF:", self.bear_off)


class Dice:
    def roll(self):
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)

        if d1 == d2:
            return [d1, d1, d1, d1]  # duble
        return [d1, d2]


class Game:
    def __init__(self):
        self.board = Board()
        self.dice = Dice()
        self.current_player = "white"
        self.moves_left = self.dice.roll()

    def print_status(self):
        print("Sıra:", self.current_player)
        print("Kalan zarlar:", self.moves_left)

    def _get_opponent(self):
        return "black" if self.current_player == "white" else "white"

    def _calculate_end(self, start, die_value):
        direction = 1 if self.current_player == "white" else -1
        if start == -1:
            return die_value - 1 if self.current_player == "white" else 24 - die_value

        return start + direction * die_value

    def _is_valid_move(self, start, die_value):
        # zar kontrolü
        if die_value not in self.moves_left:
            return False

        # start kontrolü (-1 bar için özel)
        if start != -1 and not (0 <= start <= 23):
            return False

        end = self._calculate_end(start, die_value)

        # BAR KURALI
        if self.board.bar[self.current_player] > 0:
            if start != -1:
                return False

        #  BEAR-OFF KONTROLÜ (önce yapılmalı!)
        if (end > 23 and self.current_player == "white") or (
            end < 0 and self.current_player == "black"
        ):
            if not self._all_in_home():
                return False
            return True

        #  NORMAL MOVE KONTROLLERİ

        # kaynak kontrolü (bar değilse)
        if start != -1:
            src = self.board.points[start]
            if src.owner != self.current_player or src.count == 0:
                return False

        # hedef kontrolü
        if not (0 <= end <= 23):
            return False  # güvenlik

        dst = self.board.points[end]

        # rakip 2+ taş varsa gidemez
        if dst.owner not in (None, self.current_player) and dst.count > 1:
            return False

        return True

    def _remove_from_source(self, src):
        src.count -= 1
        if src.count == 0:
            src.owner = None

    # Rakip taşı bar'a gönderme ve taşı alma işlemi

    def _handle_capture(self, dst):
        opponent = dst.owner
        if dst.count == 1:
            self.board.bar[opponent] += 1
            dst.owner = self.current_player
            dst.count = 1
        else:
            # raise Exception("Invalid move: cannot capture")
            return False

    def _apply_to_destination(self, dst):
        # Hedef noktaya taşı uygula
        if dst.owner is None:
            dst.owner = self.current_player
            dst.count = 1
        elif dst.owner == self.current_player:
            dst.count += 1
        else:
            self._handle_capture(dst)

    def _execute_move(self, start, end):

        if end > 23 or end < 0:
            if start == -1:
                self.board.bar[self.current_player] -= 1
            else:
                src = self.board.points[start]
                self._remove_from_source(src)

            self.board.bear_off[self.current_player] += 1
            return

        # normal hareket
        if start == -1:
            self.board.bar[self.current_player] -= 1
        else:
            src = self.board.points[start]
            self._remove_from_source(src)

        dst = self.board.points[end]
        self._apply_to_destination(dst)

    def _consume_die(self, die_value):
        # Kullanılan zar değerini moves_left listesinden kaldır
        self.moves_left.remove(die_value)

    def move(self, start, die_value):
        if not self._is_valid_move(start, die_value):
            return False

        end = self._calculate_end(start, die_value)
        self._execute_move(start, end)
        self._consume_die(die_value)

        if len(self.moves_left) == 0:
            self.switch_turn()
        winner = self.check_winner()
        if winner:
            print("Kazanan:", winner)
            return True
        return True

    def switch_turn(self):
        self.current_player = self._get_opponent()
        self.moves_left = self.dice.roll()
        print("Yeni sıra:", self.current_player)
        print("Yeni zarlar:", self.moves_left)
        if not self.has_any_valid_move():
            print("Geçerli hamle yok, tur geçiyor.")

            self.current_player = self._get_opponent()
            self.moves_left = self.dice.roll()
            print("Yeni sıra:", self.current_player)
            print("Yeni zarlar:", self.moves_left)

    def get_valid_moves(self):
        valid_moves = []

        if self.board.bar[self.current_player] > 0:
            for die in set(self.moves_left):
                if self._is_valid_move(-1, die):
                    end = self._calculate_end(-1, die)
                    valid_moves.append((-1, end, die))
            return valid_moves

        # normal durum
        for start in range(24):
            for die in set(self.moves_left):
                if self._is_valid_move(start, die):
                    end = self._calculate_end(start, die)
                    valid_moves.append((start, end, die))
        if len(set(self.moves_left)) == 2:  # iki farklı zar varsa
            die1, die2 = list(set(self.moves_left))

            moves_die1 = [m for m in valid_moves if m[2] == die1]
            moves_die2 = [m for m in valid_moves if m[2] == die2]

            # sadece biri oynanabiliyorsa büyük olan zorunlu
            if not moves_die1 and moves_die2:
                return moves_die2
            if not moves_die2 and moves_die1:
                return moves_die1
        return valid_moves

    def has_any_valid_move(self):
        return len(self.get_valid_moves()) > 0

    def _all_in_home(self):
        if self.current_player == "white":
            for i in range(0, 18):
                p = self.board.points[i]
                if p.owner == "white":
                    return False
        else:
            for i in range(6, 24):
                p = self.board.points[i]
                if p.owner == "black":
                    return False
        return True

    def check_winner(self):
        if self.board.bear_off["white"] == 15:
            return "white"
        if self.board.bear_off["black"] == 15:
            return "black"
        return None

    def game_state(self):
        return {
            "points": [{"owner": p.owner, "count": p.count} for p in self.board.points],
            "bar": self.board.bar,
            "bear_off": self.board.bear_off,
            "current_player": self.current_player,
            "moves_left": self.moves_left,
            "winner": self.check_winner(),
        }


# TEST
if __name__ == "__main__":
    game = Game()
    game.board.print_board()
    game.print_status()
    print("Geçerli hamleler:", game.get_valid_moves())
    first_move = game.get_valid_moves()[0]
    start, end, die = first_move

    print("Hamle sonucu:", game.move(start, die))
    game.board.print_board()
    game.print_status()
    print("Yeni geçerli hamleler:", game.get_valid_moves())
