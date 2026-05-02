import socket
import threading
import sys
import os
import queue

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.protocol import encode, decode

HOST = "127.0.0.1"
PORT = 5000

ROLL = "ROLL"
MOVE = "MOVE"

input_queue = queue.Queue()


def _input_worker():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            input_queue.put(line)
        except Exception:
            break


# Arkaplanda sürekli terminal girişlerini toplayacak thread
threading.Thread(target=_input_worker, daemon=True).start()


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

    def safe_input(self, prompt=">>> "):
        print(prompt, end="", flush=True)

        while self.running:
            try:
                # 0.2 saniyede bir input_queue'yu kontrol et
                return input_queue.get(timeout=0.2).strip()
            except queue.Empty:
                continue

        return None

    def handle_game_over(self, msg):
        log_block("OYUN BİTTİ")
        log(f"Kazanan: {msg.get('winner')}")
        if "reason" in msg:
            log(f"Sebep: {msg.get('reason')}")

        while True:
            print("Tekrar oynamak ister misiniz? (y/n): ", end="", flush=True)

            secim = ""
            while True:
                try:
                    secim = input_queue.get(timeout=0.2).strip().lower()
                    break
                except queue.Empty:
                    continue

            if secim == "y":
                return "RECONNECT"
            elif secim == "n":
                return "EXIT"
            log("Lütfen y veya n girin.")

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

                        if msg_type == "WAITING":
                            log("Rakip bekleniyor...")

                        elif msg_type == "MATCH":
                            log(f"Eşleşme sağlandı. Renk: {msg.get('color')}")

                        elif msg_type == "STATE":
                            # Terminal spam'i yapmasın, UI veya callback bunu işleyecek
                            pass

                        elif msg_type == "REJECT":
                            log(f"[HATA] {msg.get('reason')}")

                        elif msg_type == "GAME_OVER":
                            return "GAME_OVER"

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

    def handle_command(self, cmd):
        parts = cmd.split()

        if not parts:
            return

        if parts[0] == "roll":
            self.send({"type": ROLL})
            return

        if parts[0] == "move":
            if len(parts) != 3:
                log("Kullanım: move <start> <die>")
                return

            try:
                start = int(parts[1])
                die = int(parts[2])

                if start < 0 or die <= 0:
                    log("Geçersiz değerler.")
                    return

                self.send({"type": MOVE, "moves": [(start, die)]})

            except ValueError:
                log("start ve die sayı olmalıdır.")
            return

        if parts[0] in ("help", "?"):
            log("\nKomutlar: roll, move <start> <die>, quit")
            return

        if parts[0] == "quit":
            raise KeyboardInterrupt

        log("Bilinmeyen komut.")

    def start(self):
        while True:
            self.running = True
            self.game_over_msg = None

            try:
                self.connect()
            except Exception as e:
                log(f"Bağlantı hatası: {e}")
                break

            action = None

            def run_listener():
                nonlocal action
                action = self.listen()

            t = threading.Thread(target=run_listener, daemon=True)
            t.start()

            while self.running:
                try:
                    cmd = self.safe_input()

                    if not self.running:
                        break

                    if cmd is None:
                        continue

                    if not cmd:
                        continue

                    self.handle_command(cmd)

                except KeyboardInterrupt:
                    log("\nProgram sonlandırıldı.")
                    self.running = False
                    try:
                        self.sock.close()
                    except:
                        pass
                    return

            self.running = False

            try:
                self.sock.close()
            except:
                pass

            t.join(timeout=1)

            if self.game_over_msg:
                action = self.handle_game_over(self.game_over_msg)
                self.game_over_msg = None

            if action == "RECONNECT":
                log("\nYeniden bağlanılıyor...\n")
                continue
            else:
                log("Program sonlandırıldı.")
                break


if __name__ == "__main__":
    client = GameClient()
    client.start()
