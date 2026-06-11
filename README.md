# esp32-skills

Hermes Agent skills and toolchain for ESP32 development ecosystem.

**Цель:** Превратить Hermes Desktop в полноценного AI-ассистента для embedded-разработки на ESP32: от мигалки до голосового ассистента на собственном железе.

## Структура

```
esp32-skills/
├── boards/
│   ├── registry.json            # Реестр парка плат
│   └── board-1/README.md        # Heltec WiFi LoRa 32 V4
├── projects/
│   └── hello_world/             # Проверенный проект: LVGL + SSD1306
├── skills/
│   └── esp32-component-checker/ # Проверка совместимости компонентов
│       ├── SKILL.md
│       ├── scripts/parse_registry.py
│       └── templates/build_template.bat
├── Hermes_ESP32_Design_v4.md    # PRD — полный дизайн-документ
└── knowledge/                   # База знаний (TRM, даташиты)
```

## Парк плат

| Плата | Чип | Статус | Назначение |
|-------|-----|--------|------------|
| Heltec WiFi LoRa 32 V4 | ESP32-S3 | В наличии | Полигон для отладки конвейера |
| ESP32-S31-Korvo-1 | ESP32-S31 | Заказана | Основная плата: LVGL, аудио, речь, камера |

## Установка окружения

```bash
# ESP-IDF v5.5.3 (для S3)
cd /d/esp
git clone --depth 1 --branch v5.5.3 https://github.com/espressif/esp-idf.git idf55
cmd.exe //c "cd /d/esp/idf55 && install.bat esp32s3"
```

**Важно:** для работы из git-bash — `set MSYSTEM=` перед запуском .bat файлов.

## Быстрый старт

```bash
# Алиас для парсера реестра
alias esp-checker="python /c/Users/valer/AppData/Local/hermes/skills/software-development/esp32-component-checker/scripts/parse_registry.py"

# Поиск компонентов под esp32s3
esp-checker search --target esp32s3 --limit 5

# Проверка совместимости
esp-checker check lvgl/lvgl --board heltec-v4

# Инфо о компоненте
esp-checker info espressif/ssd1306
```

## Связанные проекты

- [designfordrink/troitsa](https://github.com/designfordrink/troitsa) — Multi-model decision workflow (не ESP32)

## Лицензия

MIT