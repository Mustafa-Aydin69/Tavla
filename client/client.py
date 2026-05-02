import socket
import threading
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.protocol import encode, decode

HOST = "127.0.0.1"
PORT = 5000

ROLL = "ROLL"
MOVE = "MOVE"

def log(msg):
    print(msg)

def log_block(title):
    print(f"\n=== {title} ===")


class GameClient:
    def __init__(self):
        self.running = True
        self.sock = None
        self.game_over_msg = None
        self.on_message = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOST, PORT))
        log("Sunucuya bağlanıldı.")

    def send(self, msg):
        try:
            self.sock.sendall(encode(msg))
        except Exception as e:
            log(f"[HATA] Mesaj gönderilemedi: {e}")

    def listen(self):
        buffer = ""

        while self.running:
            try:
                data = self.sock.recv(1024)

                if not data:
                    self.running = False
                    return "EXIT"

                try:
                    buffer += data.decode("utf-8")
                except UnicodeDecodeError:
                    continue

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)

                    if not line.strip():
                        continue

                    try:
                        msg = decode(line)
                        msg_type = msg.get("type")

                        if msg_type == "GAME_OVER":
                            self.game_over_msg = msg
                            self.running = False

                            if self.on_message:
                                self.on_message(msg)

                            return "GAME_OVER"

                        if self.on_message:
                            self.on_message(msg)

                        if msg_type == "WAITING":
                            log("Rakip bekleniyor...")

                        elif msg_type == "MATCH":
                            log(f"Eşleşme sağlandı. Renk: {msg.get('color')}")

                        elif msg_type == "STATE":
                            # Terminal spam'i yapmasın, UI veya callback bunu işleyecek
                            pass

                        elif msg_type == "REJECT":
                            log(f"[HATA] {msg.get('reason')}")

                        elif msg_type == "OPPONENT_DISCONNECTED":
                            log("Rakip oyundan ayrıldı.")

                    except Exception:
                        log(f"Geçersiz JSON: {line}")

            except Exception as e:
                if self.running:
                    log(f"\n[HATA] {e}")
                self.running = False
                return "EXIT"

        return "EXIT"

    def start(self):
        self.running = True
        self.game_over_msg = None

        try:
            self.connect()
        except Exception as e:
            log(f"Bağlantı hatası: {e}")
            return

        t = threading.Thread(target=self.listen, daemon=True)
        t.start()


if __name__ == "__main__":
    # Test amaçlı
    client = GameClient()
    client.start()
    
    # UI entegre edilene kadar terminal kapanmasın diye geçici blok
    try:
        while client.running:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        pass
