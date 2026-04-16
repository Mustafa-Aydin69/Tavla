import random
from tracemalloc import start

class Point:
    def __init__(self, owner=None, count=0):
        self.owner = owner  # "Siyah" veya "beyaz"
        self.count = count  # Nokta üzerindeki taş sayısı

class Board:
    def __init__(self):
        self.points = [Point() for _ in range(24)]
        
        self.bar = {
            "white": 0,
            "black": 0
        }

        self.bear_off = {
            "white": 0,
            "black": 0
        }

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
       return start + direction * die_value
    
    def _is_valid_move(self, start, die_value):
        if die_value not in self.moves_left:
            return False
        
        if not (0 <= start <= 23):
            return False        
        
        end = self._calculate_end(start, die_value)
        if end < 0 or end > 23:
            return False
        
        src = self.board.points[start]
        
        if src.owner != self.current_player or src.count == 0:
            return False
        
        dst = self.board.points[end]
        
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
            raise Exception("Invalid move: cannot capture")

    def _apply_to_destination(self, dst):
        if dst.owner is None:
            dst.owner = self.current_player
            dst.count = 1
        elif dst.owner == self.current_player:
            dst.count += 1
        else :
            self._handle_capture(dst)   
    def _execute_move(self, start, end):
        src = self.board.points[start]
        dst = self.board.points[end]
        self._remove_from_source(src)
        self._apply_to_destination(dst)
      
    def _consume_die(self, die_value):
        self.moves_left.remove(die_value)

    def move(self, start, die_value):
        if not self._is_valid_move(start, die_value):
            return False

        end = self._calculate_end(start, die_value)
        self._execute_move(start, end)
        self._consume_die(die_value)
        return True

    def switch_turn(self):
        self.current_player = self._get_opponent()
        self.moves_left = self.dice.roll()
        print("Yeni sıra:", self.current_player)
        print("Yeni zarlar:", self.moves_left)
            
    
    

    def _consume_die(self, die_value):
     self.moves_left.remove(die_value)

    def switch_turn(self):
        self.current_player = self._get_opponent()
        self.moves_left.clear()
        self.roll_dice()




# TEST
game = Game()
game.board.print_board()
game.print_status()

print("Hamle sonucu:", game.move(0, 3))
game.board.print_board()
game.print_status()