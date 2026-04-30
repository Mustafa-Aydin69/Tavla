import socket
import threading
import sys
import os

# shared.protocol importu için gerekli
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.protocol import encode, decode

HOST = "127.0.0.1"
PORT = 5000

running = True
sock = None
game_over_msg = None


def connect_to_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    print("Sunucuya bağlanıldı.")
    return s


def send_message(msg):
    global sock

    try:
        sock.sendall(encode(msg))
    except Exception as e:
        print("Mesaj gönderilemedi:", e)


def handle_game_over(msg):
    print("\n=== OYUN BİTTİ ===")
    print("Kazanan:", msg.get("winner"))
    if "reason" in msg:
        print("Sebep:", msg.get("reason"))

    while True:
        secim = input("Tekrar oynamak ister misiniz? (y/n): ").lower()

        if secim == "y":
            return "RECONNECT"
        elif secim == "n":
            return "EXIT"
        else:
            print("Lütfen y veya n girin.")


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
                        print("\n[BEKLEME] Rakip bekleniyor...")

                    elif msg_type == "MATCH":
                        print(f"\n[EŞLEŞME] Oyuna girdiniz! Renk: {msg.get('color')}")

                    elif msg_type == "STATE":
                        print("\n[OYUN DURUMU]")
                        print(f"Sıra: {msg.get('turn')}")
                        print(f"Zarlar: {msg.get('state', {}).get('moves_left')}")

                    elif msg_type == "REJECT":
                        print(f"\n[HATA] {msg.get('reason')}")

                    elif msg_type == "GAME_OVER":
                        game_over_msg = msg
                        running = False
                        return "GAME_OVER"

                    else:
                        print("\n[SERVER]", msg)

                except Exception:
                    print("Geçersiz JSON:", line)

        except Exception as e:
            if running:
                print("Dinleme hatası:", e)
            running = False
            break

    return "EXIT"


def handle_command(cmd):
    if cmd == "roll":
        send_message({"type": "ROLL"})
        return

    if cmd.startswith("move "):
        try:
            _, start, die = cmd.split()
            send_message({"type": "MOVE", "moves": [(int(start), int(die))]})
        except ValueError:
            print("Kullanım: move <start> <die>")
        return

    if cmd in ("help", "?"):
        print("Komutlar:")
        print("  roll")
        print("  move <start> <die>")
        print("  help")
        print("  quit")
        return

    if cmd == "quit":
        raise KeyboardInterrupt

    print("Bilinmeyen komut. Yardım için: help")


def start_client():
    global sock, running, game_over_msg

    while True:
        running = True
        game_over_msg = None

        try:
            sock = connect_to_server()
        except Exception as e:
            print("Bağlantı hatası:", e)
            break

        action = None

        def run_listener():
            nonlocal action
            action = listen()

        t = threading.Thread(target=run_listener, daemon=True)
        t.start()

        while running:
            try:
                cmd = input(">>> ").strip()

                if not running:
                    break

                if not cmd:
                    continue

                handle_command(cmd)

            except KeyboardInterrupt:
                print("\nÇıkılıyor...")
                running = False
                break
            except Exception as e:
                print("Hata:", e)
                running = False
                break

        running = False

        try:
            sock.close()
        except:
            pass

        t.join(timeout=1)

        if game_over_msg:
            action = handle_game_over(game_over_msg)
            game_over_msg = None

        if action is None:
            action = "EXIT"

        if action == "RECONNECT":
            print("Yeniden bağlanılıyor...\n")
            continue
        else:
            print("Program sonlandırıldı.")
            break


if __name__ == "__main__":
    start_client()
