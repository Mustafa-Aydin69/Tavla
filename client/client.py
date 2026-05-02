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
        self.thread = None

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((HOST, PORT))
            self.sock.settimeout(0.5)
            log("Sunucuya bağlanıldı.")
        except Exception as e:
            self.sock = None
            log(f"[CONNECT HATA] {e}")
            raise

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

                        if msg_type == "REJECT":
                            if not self.on_message:
                                log(f"[HATA] {msg.get('reason')}")

                    except Exception as e:
                        log(f"[JSON HATA] Veri parse edilemedi: {e} | Raw: {line}")

            except socket.timeout:
                continue
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

        self.thread = threading.Thread(target=self.listen, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

        try:
            if self.sock:
                self.sock.close()
        except Exception as e:
            log(f"[STOP HATA] {e}")

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)

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
