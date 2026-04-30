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

running = True
sock = None
game_over_msg = None


def log(msg):
    print(msg)


def log_block(title):
    print(f"\n=== {title} ===")


def connect_to_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    log("Sunucuya bağlanıldı.")
    return s


def send_message(msg):
    global sock
    try:
        sock.sendall(encode(msg))
    except Exception as e:
        log(f"[HATA] Mesaj gönderilemedi: {e}")


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

def safe_input(prompt=">>> "):
    print(prompt, end="", flush=True)

    while running:
        try:
            # 0.2 saniyede bir input_queue'yu kontrol et
            return input_queue.get(timeout=0.2).strip()
        except queue.Empty:
            continue

    return None


def handle_game_over(msg):
    log_block("OYUN BİTTİ")
    log(f"Kazanan: {msg.get('winner')}")
    if "reason" in msg:
        log(f"Sebep: {msg.get('reason')}")

    while True:
        secim = input("Tekrar oynamak ister misiniz? (y/n): ").lower()

        if secim == "y":
            return "RECONNECT"
        elif secim == "n":
            return "EXIT"
        log("Lütfen y veya n girin.")


def listen():
    global running, sock, game_over_msg
    buffer = ""

    while running:
        try:
            data = sock.recv(1024)

            if not data:
                running = False
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

                    if msg_type == "WAITING":
                        log("\n[BEKLEME] Rakip bekleniyor...")

                    elif msg_type == "MATCH":
                        log(f"\n[EŞLEŞME] Renk: {msg.get('color')}")

                    elif msg_type == "STATE":
                        log_block("OYUN DURUMU")
                        log(f"Sıra: {msg.get('turn')}")
                        log(f"Zarlar: {msg.get('state', {}).get('moves_left')}")
                        log(f"Hamleler: {msg.get('state', {}).get('valid_moves')}")

                    elif msg_type == "REJECT":
                        log(f"\n[HATA] {msg.get('reason')}")

                    elif msg_type == "GAME_OVER":
                        game_over_msg = msg
                        running = False
                        return "GAME_OVER"

                    elif msg_type == "OPPONENT_DISCONNECTED":
                        continue

                    else:
                        log(f"\n[SERVER] {msg}")

                except Exception:
                    log(f"Geçersiz JSON: {line}")

        except Exception as e:
            if running:
                log(f"\n[HATA] {e}")
            running = False
            return "EXIT"

    return "EXIT"


def handle_command(cmd):
    parts = cmd.split()

    if not parts:
        return

    if parts[0] == "roll":
        send_message({"type": ROLL})
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

            send_message({"type": MOVE, "moves": [(start, die)]})

        except ValueError:
            log("start ve die sayı olmalıdır.")
        return

    if parts[0] in ("help", "?"):
        log("\nKomutlar: roll, move <start> <die>, quit")
        return

    if parts[0] == "quit":
        raise KeyboardInterrupt

    log("Bilinmeyen komut.")


def start_client():
    global sock, running, game_over_msg

    while True:
        running = True
        game_over_msg = None

        try:
            sock = connect_to_server()
        except Exception as e:
            log(f"Bağlantı hatası: {e}")
            break

        action = None

        def run_listener():
            nonlocal action
            action = listen()

        t = threading.Thread(target=run_listener, daemon=True)
        t.start()

        while running:
            try:
                cmd = safe_input()

                if not running:
                    break

                if cmd is None:
                    continue

                if not cmd:
                    continue

                handle_command(cmd)

            except KeyboardInterrupt:
                log("\nProgram sonlandırıldı.")
                running = False
                try:
                    sock.close()
                except:
                    pass
                return

        running = False

        try:
            sock.close()
        except:
            pass

        t.join(timeout=1)

        if game_over_msg:
            action = handle_game_over(game_over_msg)
            game_over_msg = None

        if action == "RECONNECT":
            log("\nYeniden bağlanılıyor...\n")
            continue
        else:
            log("Program sonlandırıldı.")
            break


if __name__ == "__main__":
    start_client()
