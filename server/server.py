import socket
import threading
import sys
import os
import json
import logging

# Loglama ayarları
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Server")

# shared.protocol importu için gerekli
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from shared.protocol import decode, encode


def send_safe(conn, msg):
    try:
        conn.sendall(encode(msg))
    except Exception as e:
        logger.error(f"Send failed: {e}")


class ClientContext:
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.opponent = None
        self.game = None
        self.color = None


class GameSession:
    def __init__(self, p1, p2):
        from game import Game

        self.game = Game()
        self.players = [p1, p2]
        self.lock = threading.Lock()

        p1.game = self
        p2.game = self


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
                    logger.error(f"Decode error from {client.addr}: {e}")
                    continue
            except socket.timeout:
                logger.warning(f"Connection timeout (AFK) from {client.addr}")
                normal_disconnect = False
                break
            except Exception as e:
                logger.error(f"Error receiving data from {client.addr}: {e}")
                break

            buffer += data

            # Buffer overflow koruması
            if len(buffer) > 10000:
                logger.warning(f"Buffer overflow from {client.addr}")
                break

            # Mesajları newline (\n) karakterine göre ayırıyoruz
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)

                # Boş satırları atlama
                if line.strip():
                    try:
                        msg = decode(line)
                        logger.debug(f"Received from {client.addr}: {msg.get('type')}")

                        if msg.get("type") == "MOVE":
                            session = client.game
                            if not session:
                                continue

                            with session.lock:
                                moves = msg.get("moves")
                                if not isinstance(moves, list):
                                    send_safe(
                                        client.conn,
                                        {"type": "REJECT", "reason": "Invalid format"},
                                    )
                                    continue

                                # 2. Sıra kontrolü
                                if session.game.current_player != client.color:
                                    send_safe(
                                        client.conn,
                                        {"type": "REJECT", "reason": "Not your turn"},
                                    )
                                    continue

                                # 3. Move uygulama
                                success = session.game.apply_move_sequence(moves)

                                # 4. Başarısızsa REJECT
                                if not success:
                                    send_safe(
                                        client.conn,
                                        {"type": "REJECT", "reason": "Invalid move"},
                                    )
                                    continue

                                # 5. STATE oluştur
                                if not session.game:
                                    continue

                                state = session.game.get_state()
                                turn_color = session.game.current_player
                                last_player = (
                                    "black" if turn_color == "white" else "white"
                                )

                                # 6. İki oyuncuya gönder
                                for p in session.players:
                                    send_safe(
                                        p.conn,
                                        {
                                            "type": "STATE",
                                            "state": state,
                                            "turn": turn_color,
                                            "last_player": last_player,
                                        },
                                    )

                                # 8. Kazanma kontrolü (opsiyonel)
                                # is_game_over() fonksiyonu True/False dönecek
                                if (
                                    session.game
                                    and hasattr(session.game, "is_game_over")
                                    and session.game.is_game_over()
                                ):
                                    winner = session.game.get_winner()
                                    for p in session.players:
                                        send_safe(
                                            p.conn,
                                            {"type": "GAME_OVER", "winner": winner},
                                        )
                                        p.game = None
                                        p.opponent = None

                                    # Profesyonel temizlik
                                    session.players.clear()
                                    session.game = None

                    except json.JSONDecodeError as e:
                        logger.error(
                            f"Invalid JSON from {client.addr}: {e} (Line: {line})"
                        )
                    except Exception as e:
                        logger.error(f"Decode/Processing error from {client.addr}: {e}")
                        send_safe(
                            client.conn, {"type": "REJECT", "reason": "Server error"}
                        )

    except Exception as e:
        # Beklenmedik bir şekilde bağlantı koparsa buraya düşer
        logger.error(f"Error with {client.addr}: {e}")
    finally:
        # Bağlantı koptuğunda durumu belirterek çalışır
        if normal_disconnect:
            logger.info(f"Client disconnected normally: {client.addr}")
        else:
            logger.warning(f"Client disconnected with error/abruptly: {client.addr}")

        # Eğer eşleşmiş bir rakip varsa ona bağlantının koptuğunu bildir
        if client.opponent and client.opponent.conn:
            send_safe(client.opponent.conn, {"type": "OPPONENT_DISCONNECTED"})
            client.opponent.opponent = None

        # Queue'da kalmış ölü client'ı temizle
        with waiting_lock:
            if client in waiting_players:
                waiting_players.remove(client)

        # Oyundan kopan varsa GameSession temizliği ve oyunu bitirme
        if client.game:
            session = client.game
            for p in session.players:
                send_safe(
                    p.conn, {"type": "GAME_OVER", "reason": "Opponent disconnected"}
                )
                p.game = None
                p.opponent = None

            session.players.clear()
            session.game = None

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

    logger.info(f"Server listening on {HOST}:{PORT}...")

    try:
        while True:
            # Bağlantı bekle ve kabul et
            client_socket, client_address = server_socket.accept()

            print(f"New connection: {client_address}")

            # Bağlantıya 5 dakikalık (300 saniye) eylemsizlik (AFK) sınırı koy
            client_socket.settimeout(300.0)

            # Client'ı obje haline getir
            client = ClientContext(client_socket, client_address)

            # Ayrı bir thread başlat ve client ile iletişimi anında oraya devret
            # daemon=True sayesinde ana program kapanınca thread'ler de arkada asılı kalmaz, kapanır.
            threading.Thread(target=handle_client, args=(client,), daemon=True).start()

            # Thread-safe şekilde sıraya ekle ve eşleştir
            with waiting_lock:
                waiting_players.append(client)
                send_safe(client.conn, {"type": "WAITING"})

                # 2 oyuncu olunca eşleştir
                if len(waiting_players) >= 2:
                    p1 = waiting_players.pop(0)
                    p2 = waiting_players.pop(0)

                    # Rakipleri birbirine bağla (Çok Kritik!)
                    p1.opponent = p2
                    p2.opponent = p1

                    p1.color = "white"
                    p2.color = "black"

                    # GameSession oluştur
                    session = GameSession(p1, p2)

                    # MATCH mesajlarını gönder
                    send_safe(p1.conn, {"type": "MATCH", "color": "white"})
                    send_safe(p2.conn, {"type": "MATCH", "color": "black"})

                    logger.info(f"[MATCH] {p1.addr} vs {p2.addr}")

                    # MATCH sonrası INITIAL STATE gönder (Böylece Client boş ekranla başlamaz)
                    if hasattr(session.game, "get_state"):
                        state = session.game.get_state()
                        turn_color = session.game.current_player
                        send_safe(
                            p1.conn,
                            {"type": "STATE", "state": state, "turn": turn_color},
                        )
                        send_safe(
                            p2.conn,
                            {"type": "STATE", "state": state, "turn": turn_color},
                        )

    except KeyboardInterrupt:
        logger.info("Server shutting down.")
    finally:
        server_socket.close()


if __name__ == "__main__":
    start_server()
