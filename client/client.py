import socket

HOST = "127.0.0.1"
PORT = 5000


def start_client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    print("Connected to server")
    while True:
        data = sock.recv(1024)
        if not data:
            print("Server stopped")
            break
        print(f"Server: {data.decode()}")


if __name__ == "__main__":
    start_client()
