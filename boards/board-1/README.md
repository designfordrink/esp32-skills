# board-1: Heltec WiFi LoRa 32 V4

| Характеристика | Значение |
|---|---|
| **Чип** | ESP32-S3R2 (Xtensa LX7 dual-core) |
| **Flash** | 16 MB |
| **PSRAM** | 8 MB (OPI) |
| **Дисплей** | OLED 0.96" 128×64, SSD1306, I2C |
| **LoRa** | SX1262 (не используется в v4) |
| **Кнопка** | GPIO0 (boot), RST |
| **LED** | GPIO37 (на некоторых ревизиях, уточнять) |
| **Разъём** | USB-C (CH340 или CP210x) |

### Pinout (предварительный, уточнить по TRM при получении платы)
- OLED I2C: SDA=GPIO17, SCL=GPIO18
- OLED RST: GPIO21
- Кнопка: GPIO0
- LED: GPIO37
- LoRa: SPI (CS=GPIO8, SCK=GPIO9, MOSI=GPIO10, MISO=GPIO11, RST=GPIO12, BUSY=GPIO13)

### История прошивок
| Дата | Версия | Метод | Коммит |
|---|---|---|---|
| - | - | - | - |