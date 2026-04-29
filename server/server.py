import socket
import threading
import sys
import os
import json

# shared.protocol importu için gerekli
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.protocol import decode, encode

class ClientContext:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.opponent = None
        self.game = None

# Bağlanan oyuncuların atıldığı global liste ve lock
waiting_players = []
waiting_lock = threading.Lock()

def handle_client(client: ClientContext):
    buffer = ""
    normal_disconnect = False

    try:
        while True:
            try:
                # Gelen veriyi okuma ve decode etme. Hata olursa server çökmesin.
                raw = client.conn.recv(1024)
                if not raw:
                    normal_disconnect = True
                    break
                try:
                    data = raw.decode("utf-8")
                except UnicodeDecodeError as e:
                    print(f"Decode error from {client.addr}: {e}")
                    continue

            except Exception as e:
                print(f"Error receiving data from {client.addr}: {e}")
                break

            buffer += data

            # Mesajları newline (\n) karakterine göre ayırıyoruz
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)

                # Boş satırları atlama
                if line.strip():
                    try:
                        msg = decode(line)
                        print(f"Received from {client.addr}: {msg}")
                    except json.JSONDecodeError as e:
                        print(f"Invalid JSON from {client.addr}: {e} (Line: {line})")
                    except Exception as e:
                        print(f"Decode error from {client.addr}: {e}")

    except Exception as e:
        # Beklenmedik bir şekilde bağlantı koparsa buraya düşer
        print(f"Error with {client.addr}: {e}")
    finally:
        # Bağlantı koptuğunda durumu belirterek çalışır
        if normal_disconnect:
            print(f"Client disconnected normally: {client.addr}")
        else:
            print(f"Client disconnected with error/abruptly: {client.addr}")

        # Eğer eşleşmiş bir rakip varsa ona bağlantının koptuğunu bildir
        if client.opponent and client.opponent.conn:
            try:
                client.opponent.conn.sendall(
                    encode({"type": "OPPONENT_DISCONNECTED"})
                )
                client.opponent.opponent = None
            except:
                pass

        # Queue'da kalmış ölü client'ı temizle
        with waiting_lock:
            if client in waiting_players:
                waiting_players.remove(client)

        client.conn.close()


def start_server():
    HOST = "0.0.0.0"
    PORT = 5000

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Serveri aç kapa yaptığımız zaman 5000 portu dolu gözükmesin diye "Address already in use"
    # hatasını almamak için bu satırı ekledim.(Nurettin'e Not)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((HOST, PORT))

    # Listen backlog eklenmesi (Aynı anda bekleyen bağlantı sırası)
    server_socket.listen(5)

    print(f"Server listening on {HOST}:{PORT}...")

    try:
        while True:
            # Bağlantı bekle ve kabul et
            client_socket, client_address = server_socket.accept()

            print(f"New connection: {client_address}")

            # Client'ı obje haline getir
            client = ClientContext(client_socket, client_address)

            # Ayrı bir thread başlat ve client ile iletişimi anında oraya devret
            # daemon=True sayesinde ana program kapanınca thread'ler de arkada asılı kalmaz, kapanır.
            threading.Thread(
                target=handle_client, args=(client,), daemon=True
            ).start()

            # Thread-safe şekilde sıraya ekle ve eşleştir
            with waiting_lock:
                waiting_players.append(client)
                client.conn.sendall(encode({"type": "WAITING"}))

                # 2 oyuncu olunca eşleştir
                if len(waiting_players) >= 2:
                    p1 = waiting_players.pop(0)
                    p2 = waiting_players.pop(0)

                    # Rakipleri birbirine bağla (Çok Kritik!)
                    p1.opponent = p2
                    p2.opponent = p1

                    # MATCH mesajlarını gönder
                    p1.conn.sendall(encode({"type": "MATCH", "color": "WHITE"}))
                    p2.conn.sendall(encode({"type": "MATCH", "color": "BLACK"}))

                    print(f"[MATCH] {p1.addr} vs {p2.addr}")

    except KeyboardInterrupt:
        print("\nServer shutting down.")
    finally:
        server_socket.close()


if __name__ == "__main__":
    start_server()
