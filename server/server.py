import socket
import threading
import sys
import os

# shared.protocol importu için gerekli
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.protocol import decode

def handle_client(conn, addr):
    buffer = ""
    try:
        while True:
            data = conn.recv(1024).decode("utf-8")
            if not data:
                # Eğer recv() boş dönerse client bağlantıyı normal şekilde kapatmış
                break
                
            buffer += data
            
            # Mesajları newline (\n) karakterine göre ayırıyoruz
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                
                # Boş satırları atlama
                if line.strip():
                    msg = decode(line)
                    print(f"Received from {addr}: {msg}")
                    
    except Exception as e:
        # Beklenmedik bir şekilde bağlantı koparsa buraya düşer
        pass
    finally:
        #bağlantı koptuğunda çalışır
        print(f"Client disconnected: {addr}")
        conn.close()

def start_server():
    HOST = "0.0.0.0"
    PORT = 5000

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    #Serveri aç kapa yaptığımız zaman 5000 portu dolu gözükmesin diye "Address already in use"
    #hatasını almamak için bu satırı ekledim.(Nurettin'e Not)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print(f"Server listening on {HOST}:{PORT}...")

    try:
        while True:
            # Bağlantı bekle ve kabul et
            client_socket, client_address = server_socket.accept()
            
            print(f"New connection: {client_address}")
            
            # Ayrı bir thread başlat ve client ile iletişimi oraya devret
            # daemon=True sayesinde ana program kapanınca thread'ler de arkada asılı kalmaz, kapanır.
            threading.Thread(target=handle_client, args=(client_socket, client_address), daemon=True).start()
            
    except KeyboardInterrupt:
        print("\nServer shutting down.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()
