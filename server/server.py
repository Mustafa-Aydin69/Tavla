import socket
import threading
import sys
import os
import json

# shared.protocol importu için gerekli
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.protocol import decode, encode

# Bağlanan oyuncuların atıldığı global liste
waiting_players = []


def handle_client(conn, addr):
    buffer = ""
    normal_disconnect = False

    try:
        while True:
            try:
                # Gelen veriyi okuma ve decode etme. Hata olursa server çökmesin.
                raw = conn.recv(1024)
                if not raw:
                    normal_disconnect = True
                    break
                try:
                    data = raw.decode("utf-8")
                except UnicodeDecodeError as e:
                    print(f"Decode error from {addr}: {e}")
                    continue

            except Exception as e:
                print(f"Error receiving data from {addr}: {e}")
                break

            if not data:
                # Eğer recv() boş dönerse client bağlantıyı normal şekilde kapatmış
                normal_disconnect = True
                break

            buffer += data

            # Mesajları newline (\n) karakterine göre ayırıyoruz
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)

                # Boş satırları atlama
                if line.strip():
                    try:
                        msg = decode(line)
                        print(f"Received from {addr}: {msg}")
                    except json.JSONDecodeError as e:
                        print(f"Invalid JSON from {addr}: {e} (Line: {line})")
                    except Exception as e:
                        print(f"Decode error from {addr}: {e}")

    except Exception as e:
        # Beklenmedik bir şekilde bağlantı koparsa buraya düşer
        print(f"Error with {addr}: {e}")
    finally:
        # Bağlantı koptuğunda durumu belirterek çalışır
        if normal_disconnect:
            print(f"Client disconnected normally: {addr}")
        else:
            print(f"Client disconnected with error/abruptly: {addr}")

        conn.close()


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

            # Bağlanan client'ı sıraya ekle
            waiting_players.append((client_socket, client_address))

            # WAITING mesajı gönder
            client_socket.sendall(encode({"type": "WAITING"}))

            # 2 oyuncu olunca eşleştir
            if len(waiting_players) >= 2:
                p1_sock, p1_addr = waiting_players.pop(0)
                p2_sock, p2_addr = waiting_players.pop(0)

                # MATCH mesajlarını gönder
                p1_sock.sendall(encode({"type": "MATCH", "color": "WHITE"}))
                p2_sock.sendall(encode({"type": "MATCH", "color": "BLACK"}))

                print(f"Match found: {p1_addr} vs {p2_addr}")

            # Ayrı bir thread başlat ve client ile iletişimi oraya devret
            # daemon=True sayesinde ana program kapanınca thread'ler de arkada asılı kalmaz, kapanır.
            # İşletim sistemi projesinde yaptığımız aynı işlem
            threading.Thread(
                target=handle_client, args=(client_socket, client_address), daemon=True
            ).start()

    except KeyboardInterrupt:
        print("\nServer shutting down.")
    finally:
        server_socket.close()


if __name__ == "__main__":
    start_server()
