---
name: esp32-component-checker
description: "Use when adding ESP-IDF components from components.espressif.com — check compatibility with a specific board (chip + interfaces), generate idf.py add-dependency commands, and run a verified build. Covers: parsing the component registry, matching 'Supports all targets' / target list against board chip, filtering by I2C/SPI/GPIO interface, generating dependencies, and building with proper MSYS-free environment."
version: 1.0.0
author: Hermes (for Жорик's ESP32 environment)
license: MIT
tags: [esp32, esp-idf, components, lvgl, ssd1306, registry, build, heltec, esp32s3]
---

# ESP32 Component Checker

Проверка совместимости компонентов из `components.espressif.com` с конкретной платой, генерация зависимостей и сборка.

## Когда использовать

- Нужно добавить компонент (LVGL, SSD1306, драйвер дисплея, etc.) в ESP-IDF проект
- Неизвестно, будет ли компонент работать на конкретной плате (Heltec V4, Korvo-1)
- Нужно сгенерировать `idf.py add-dependency` и проверить сборкой
- Нужно найти все компоненты под esp32s3 / esp32s31

**НЕ использовать** для:
- Простого hello_world без внешних компонентов
- Компонентов, которые уже в IDF из коробки

## Процесс

### 1. Узнать спецификацию платы

Из `boards/registry.json` или `boards/board-N/README.md` взять:

| Параметр | Heltec V4 | Korvo-1 |
|----------|-----------|---------|
| Чип | esp32s3 | esp32s31 |
| Дисплей | SSD1306 (I2C, 128×64) | LCD 4.3" 800×480 + LVGL |
| I2C | SDA=GPIO17, SCL=GPIO18 | Есть |
| Кнопка | GPIO0 | Есть |
| LED | GPIO37 | — |
| Аудио | — | Два микрофона + стерео-динамики |
| Камера | — | OV3660 3MP |

### 2. Найти компоненты через API

Скрипт `parse_registry.py` использует официальный REST API:
`https://components.espressif.com/api/components?q=<query>`

Ключевые запросы (через `esp-checker` alias или полный путь):

```bash
# Поиск по чипу — префикс target: обязателен
esp-checker search --target esp32s3 --limit 10

# Поиск по чипу + ключевому слову
esp-checker search --target esp32s3 --query ssd1306

# Поиск по ключевому слову (без фильтра чипа)
esp-checker search --query lvgl
```

**Синтаксис query:**
- `target:esp32s3` — компоненты, поддерживающие чип (основной режим)
- `ssd1306` — по имени/описанию
- `target:esp32s3 ssd1306` — комбинация (поддерживает чип И содержит слово)

**Форматы вывода (флаг `--format`):**

| Формат | Описание | Когда использовать |
|--------|----------|-------------------|
| `box` (по умолчанию) | ASCII-боксы с боксами и переносом строк | Терминал, Hermes-чат |
| `html` | HTML-таблица со стилями | Браузер, Obsidian |
| `json` | Сырой JSON | Другая обработка |

**Вывод в box-формате не использует emoji** (✅ ❌ → [OK] [FAIL]) — квадратики не отображаются в некоторых терминалах.

**Ссылки на GitHub и документацию** показываются в `info` и не обрезаются — длинные URL переносятся на следующую строку бокса.

### 3. Проверить совместимость с платой

```python
# Логика проверки:
def is_compatible(component_info, board_spec):
    # 1. Чип: "Supports all targets" → YES
    #         явный список → target in list
    # 2. Интерфейс: I2C → у платы есть I2C?
    #               SPI → у платы есть SPI?
    #               GPIO → у платы есть свободный GPIO?
    # 3. Примеры: есть пример под нашу конфигурацию?
    return True/False
```

**Реальные примеры для Heltec V4:**

| Компонент | Совместимость | Почему |
|-----------|--------------|--------|
| `lvgl/lvgl^9.5.0` | [OK] | Supports all targets, чистая GUI |
| `espressif/esp_lvgl_port^2.8.0` | [OK] | Supports all targets, есть пример i2c_oled |
| `espressif/ssd1306^1.0.5` | [OK] | Supports all targets, I2C — совпадает с OLED Heltec |
| `espressif/button^4.1.7` | [OK] | Supports all targets, GPIO — подходит под кнопку Heltec |
| `espressif/led_strip^3.0.3` | [OK] | Supports all targets, но для LED на GPIO37 не нужен |

### 4. Сгенерировать зависимости

```bash
cd /d/ESP32/projects/<project>
idf.py add-dependency "lvgl/lvgl^9.5.0"
idf.py add-dependency "espressif/esp_lvgl_port^2.8.0"
idf.py add-dependency "espressif/ssd1306^1.0.5"
```

Результат — `main/idf_component.yml`:
```yaml
dependencies:
  idf:
    version: '>=4.1.0'
  lvgl/lvgl: ^9.5.0
  espressif/esp_lvgl_port: ^2.8.0
  espressif/ssd1306: ^1.0.5
```

### 5. Собрать проект (без зависаний)

**Правильный способ сборки** — через `.bat` файл, запущенный через `cmd.exe //c` в фоне:

```batch
@echo off
set MSYSTEM=
set IDF_PATH=D:\esp\idf55
set IDF_TOOLS_PATH=C:\Users\valer\.espressif

set TOOLS_BASE=%IDF_TOOLS_PATH%\tools
set PYTHON_ENV=%IDF_TOOLS_PATH%\python_env\idf5.5_py3.14_env\Scripts
set CMAKE_BIN=%TOOLS_BASE%\cmake\3.30.2\bin
set NINJA_BIN=%TOOLS_BASE%\ninja\1.12.1
set TOOLCHAIN=%TOOLS_BASE%\xtensa-esp-elf\esp-14.2.0_20251107\xtensa-esp-elf\bin
set PATH=%PYTHON_ENV%;%CMAKE_BIN%;%NINJA_BIN%;%TOOLCHAIN%;%IDF_PATH%\tools;%PATH%

cd /d D:\ESP32\projects\<project>
python %IDF_PATH%\tools\idf.py build
```

Запуск из Hermes:
```
terminal(
    command='cmd.exe //c "C:\\path\\to\\build.bat"',
    background=True,
    notify_on_complete=True,
    timeout=600
)
```

### 5b. Паттерн безопасного запуска сборки (Safe Build Loop)

Этот паттерн исключает «зависания» и даёт прозрачность на каждом шаге.

**Пошаговый протокол для Hermes:**

```
# ШАГ 1 — Подготовить .bat файл
write_file(path="D:\\ESP32\\projects\\<project>\\build.bat",
           content=batch_template_с_полным_окружением)

# ШАГ 2 — Запустить в фоне с notify
terminal(command='cmd.exe //c "...\\build.bat"',
         background=True,
         notify_on_complete=True,
         timeout=600)

# ШАГ 3 — Сразу проверить, что процесс стартовал
process(action='poll')
# status='running' → ждём notify
# status='exited', exit_code!=0 → ошибка запуска

# ШАГ 4 — Периодически проверять прогресс
process(action='poll')  # последние строки вывода

# ШАГ 5 — После notify_on_complete — полный лог
process(action='log')

# ШАГ 6 — Анализ результата
# BUILD SUCCESS [OK]
# BUILD FAILED [FAIL] -> читать build/log/idf_py_stderr_output_*.txt
```

**Что именно решает проблему «зависаний»:**

| Проблема | Решение |
|----------|---------|
| foreground блокирует сессию | background=True |
| Нет сигнала о завершении | notify_on_complete=True |
| Вывод потерян из-за tail | Нет пайпов в команде |
| MSYSTEM ломает bat | set MSYSTEM= в начале bat |
| Python не тот | Явный PATH на IDF venv + cmake + ninja + toolchain |
| Долгая сборка submodule-ов | timeout=600 — 10 минут |
| Не видно прогресса | process(action=poll) в любой момент |

**Структура проекта:**

```
D:\ESP32\projects\<project>\
├── build.bat              # из templates/build_template.bat
├── CMakeLists.txt
├── main/
│   ├── main.c
│   ├── CMakeLists.txt
│   └── idf_component.yml
└── build/
    ├── <project>.bin
    └── log/
        ├── idf_py_stdout_output_*.txt
        └── idf_py_stderr_output_*.txt
```

**Единый запуск из Hermes:**
```
terminal(command='cmd.exe //c "D:\\ESP32\\projects\\<project>\\build.bat"',
         background=True, notify_on_complete=True, timeout=600)
```

Никаких `| tail`, `source export.sh`, `python /d/.../idf.py` без venv.

### 6. Интерпретировать результат

| Исход | Что делать |
|-------|-----------|
| BUILD SUCCESS [OK] | Компонент совместим. Можно прошивать |
| BUILD FAILED [FAIL] | Смотреть вывод: ошибка компиляции — исправить код; несовместимый API — искать другую версию |
| Долгая сборка | Первый билд тянет submodule-ы через idf.py — это нормально, ждать 5-10 мин |

## Быстрый вызов (alias)

```bash
echo 'alias esp-checker="python /c/Users/valer/AppData/Local/hermes/skills/software-development/esp32-component-checker/scripts/parse_registry.py"' >> ~/.bashrc
source ~/.bashrc
```

После этого:
```bash
esp-checker search --target esp32s3 --limit 5
esp-checker info espressif/ssd1306
esp-checker check lvgl/lvgl --board heltec-v4
```

## Common Pitfalls

1. **MSYSTEM блокирует .bat.** Все IDF .bat файлы проверяют `MSYSTEM` и вылетают. Решение: `set MSYSTEM=` в начале скрипта.

2. **Shallow clone без submodule-ов.** `git clone --depth 1` не тянет подмодули. `idf.py build` сам инициализирует их при первой сборке — это нормально, ждать 5-10 мин. Не прерывать.

3. **python /d/.../idf.py без venv.** Нужно явно добавить `.espressif/python_env/idf5.5_py3.14_env/Scripts` в PATH.

4. **tail в фоновых процессах.** Буферизирует вывод, процесс выглядит зависшим. Не использовать пайпы в процессах с notify_on_complete.

5. **foreground без background.** Долгий билд блокирует сессию. Всегда `background=True + notify_on_complete=True`.

6. **IDF v5.5.3-dirty.** После сборки idf.py показывает `v5.5.3-dirty`. Это косметика, на сборку не влияет.

7. **Поиск без префикса target:.** `?q=esp32s3` ищет по имени, а не по совместимости с чипом. `--target` сам добавляет префикс.

8. **Emoji (✅❌★) как квадратики.** В некоторых терминалах emoji не отображаются. Вывод `box` использует только ASCII: [OK], [FAIL], [--].

## Verification Checklist

- [ ] Компонент найден в реестре
- [ ] Совместимость с чипом подтверждена
- [ ] Интерфейс компонента совпадает с периферией платы
- [ ] idf.py add-dependency выполнен без ошибок
- [ ] idf.py build завершён успешно (exit code 0)
- [ ] Бинарник создан (build/\<project\>.bin)
- [ ] Результат зафиксирован в boards/board-N/README.md

## References

- `references/api-endpoints.md` — документированные REST API эндпоинты компонентного реестра
- `references/verified-build-2026-06-10.md` — данные подтверждённой сборки LVGL + SSD1306 на Heltec V4 (1383/1383 targets)