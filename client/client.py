import socket


from shared.protocol import encode, decode

HOST = "127.0.0.1"
PORT = 5000


def start_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
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
                print("Usage: move <start> <die>")

        data = sock.recv(1024)
        if not data:
            print("Disconnected.")
            break

        print("SERVER:", data.decode())


if __name__ == "__main__":
    start_client()
