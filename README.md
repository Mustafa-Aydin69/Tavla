# 🎲 Tavla (Backgammon) – Multiplayer GUI Projesi

Bu proje, Python kullanılarak geliştirilmiş, gerçek zamanlı (real-time) iki oyunculu bir **Tavla (Backgammon)** oyunudur.  
Uygulama, client-server mimarisi ile çalışır ve PyQt tabanlı grafiksel arayüz (GUI) içerir.

---

## 🚀 Özellikler

- 🎮 Gerçek zamanlı iki oyunculu oyun (multiplayer)
- 🔌 TCP socket tabanlı client-server mimarisi
- 🧠 Server-side game logic (tüm kurallar sunucu tarafından yönetilir)
- 🖥️ PyQt GUI arayüz
- 🎲 Zar atma sistemi (double zar desteği)
- ✅ Geçerli hamlelerin otomatik hesaplanması
- 🟡 Geçerli hamlelerin UI’da gösterimi (highlight)
- 🟢 Seçili taşın vurgulanması
- 🪵 Bar (kırılan taşlar) sistemi
- 🏁 Bear off (oyundan çıkan taşlar)
- 🔄 Oyun sonu ve yeniden oynama (restart)
- 📡 Senkronize oyun durumu (state-based update)

---

## 🧱 Mimari Yapı

Proje, **client-server** mimarisi üzerine kuruludur:

### 🔹 Server
- Oyun mantığını yönetir
- Zar atma, hamle doğrulama ve oyun akışını kontrol eder
- Tüm state bilgisini üretir ve client’lara gönderir

### 🔹 Client
- Kullanıcı arayüzünü (UI) sağlar
- Kullanıcıdan input alır
- Server’dan gelen state’e göre UI’ı günceller

---

## 📡 Kullanılan Teknolojiler

| Alan | Teknoloji |
|------|-----------|
| Dil | Python |
| UI | PyQt |
| Network | Socket (TCP) |
| Veri Formatı | JSON |
| Mimari | Client-Server |

---

## 🧠 Oyun Mantığı

- Oyun server tarafından yönetilir (authoritative server)
- Client sadece komut gönderir (`ROLL`, `MOVE`)
- Server geçerli hamleleri hesaplar ve state olarak gönderir

### 🔑 State İçeriği:

```json
{
  "points": [...],
  "bar": { "white": 0, "black": 1 },
  "bear_off": { "white": 3, "black": 2 },
  "current_player": "white",
  "dice": [3, 5],
  "valid_moves": [[-1, 18], [-1, 23]]
}
