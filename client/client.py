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
                    print("SERVER:", msg)

                    if msg.get("type") == "GAME_OVER":
                        game_over_msg = msg
                        return "GAME_OVER"

                except Exception:
                    print("Geçersiz JSON:", line)

        except Exception as e:
            if running:
                print("Dinleme hatası:", e)
            break

    return "EXIT"


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
            global running
            running = False

        t = threading.Thread(target=run_listener, daemon=True)
        t.start()

        while running:
            try:
                cmd = input(">>> ")

                if not running:
                    break

                if cmd == "roll":
                    sock.sendall(encode({"type": "ROLL"}))

                elif cmd.startswith("move"):
                    try:
                        _, start, die = cmd.split()
                        sock.sendall(
                            encode({"type": "MOVE", "moves": [(int(start), int(die))]})
                        )
                    except ValueError:
                        print("Kullanım: move <start> <die>")

            except KeyboardInterrupt:
                print("\nÇıkılıyor...")
                running = False
                break
            except Exception as e:
                print("Hata:", e)
                break

        # Socket temizliği
        try:
            sock.close()
        except:
            pass

        # GAME_OVER geldiyse kullanıcıya sor
        if game_over_msg:
            action = handle_game_over(game_over_msg)
            game_over_msg = None

        # reconnect / exit
        if action == "RECONNECT":
            print("Yeniden bağlanılıyor...\n")
            continue
        else:
            print("Program sonlandırıldı.")
            break


if __name__ == "__main__":
    start_client()
