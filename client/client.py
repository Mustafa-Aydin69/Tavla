import socket
import threading

from shared.protocol import encode, decode

HOST = "127.0.0.1"
PORT = 5000


def listen(sock):
    buffer = ""

    while True:
        try:
            data = sock.recv(1024)
            if not data:
                print("Bağlantı kesildi.")
                break

            try:
                buffer += data.decode("utf-8")
            except UnicodeDecodeError:
                continue

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)

                if not line.strip():
                    continue

                print("SERVER:", line)

        except Exception as e:
            print("Dinleme hatası:", e)
            break


def start_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    threading.Thread(target=listen, args=(sock,), daemon=True).start()
    print("Connected to server")
    while True:
        cmd = input(">>> ")

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


if __name__ == "__main__":
    start_client()
