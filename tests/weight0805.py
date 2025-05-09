import sys
from pathlib import Path
from loguru import logger
from time import sleep

# Добавляем папку src в путь поиска модулей
sys.path.append(str(Path(__file__).resolve().parent.parent / 'src'))

from _config_manager import ConfigManager
import _lib_pcf as lib

config_manager = ConfigManager()

# Параметры детекции и стабилизации
PRESENCE_THRESHOLD = 20         # минимальный вес, чтобы считать, что животное на весах
STABILITY_THRESHOLD = 0.5       # максимальное отклонение (кг) для стабильного состояния
STABLE_DURATION = 3             # время (сек), в течение которого показания должны оставаться стабильными

# Настройка логера
logger.remove()
logger.add(
    sys.stderr,
    format="{time:HH:mm:ss.SSS} | {level} | {file}:{line} | {message}",
    level="DEBUG"
)

def main():
    arduino = None
    try:
        logger.info('\033[1;35mFeeder project. Stable weight detection test.\033[0m')
        # Калибровка и старт
        lib._calibrate_or_start()
        arduino = lib.start_obj()
        sleep(1)  # даём время Arduino «прогреться» и установить связь

        # Бесконечный цикл измерений
        while True:
            stable_w = lib.wait_for_stable_weight(
                arduino,
                presence_thr=PRESENCE_THRESHOLD,
                stability_thr=STABILITY_THRESHOLD,
                stable_duration=STABLE_DURATION
            )
            logger.info(f"Stable weight detected: {stable_w:.2f} kg\n")
            sleep(0.5)

    except KeyboardInterrupt:
        logger.info("Test interrupted by user.")
    except Exception as e:
        logger.error(f"Test error: {e}")
    finally:
        if arduino:
            logger.info("Disconnecting Arduino.")
            arduino.disconnect()

if __name__ == "__main__":
    main()
