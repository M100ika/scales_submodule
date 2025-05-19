import sys
import time
import statistics
from collections import deque
from pathlib import Path
from loguru import logger
from time import sleep
from typing import Optional, Callable

# Добавляем папку src в путь поиска модулей
sys.path.append(str(Path(__file__).resolve().parent.parent / 'src'))

from _config_manager import ConfigManager
import _lib_pcf as lib

config_manager = ConfigManager()

# Параметры детекции и стабилизации
PRESENCE_THRESHOLD = 20        # кг, считать, что животное есть на весах
STABILITY_THRESHOLD = 0.5      # кг, максимальное отклонение от медианы
STABLE_DURATION = 3            # секунды, стабильное состояние
WINDOW_SIZE = 10               # сколько последних замеров держать в буфере

# Настройка логера
logger.remove()
logger.add(
    sys.stderr,
    format="{time:HH:mm:ss.SSS} | {level} | {file}:{line} | {message}",
    level="DEBUG"
)


def create_stable_weight_detector(
    presence_thr: float,
    stability_thr: float,
    stable_duration: float,
    window_size: int
) -> Callable[[float], Optional[float]]:
    window_buf = deque(maxlen=window_size)
    valid_readings = []
    stable_start = None

    def detector(w: float) -> Optional[float]:
        nonlocal stable_start
        window_buf.append(w)
        med = statistics.median(window_buf)

        # фильтрация выбросов
        if abs(w - med) <= stability_thr:
            valid_readings.append(w)
        else:
            # выброс — игнорируем
            pass

        # проверяем присутствие
        if med >= presence_thr:
            if stable_start is None:
                stable_start = time.time()
            elif time.time() - stable_start >= stable_duration:
                # стабильность достигнута
                return statistics.median(valid_readings)
        else:
            # сбрасываем при уходе вниз
            stable_start = None
            valid_readings.clear()

        return None

    return detector


def main():
    arduino = None
    try:
        logger.info('\033[1;35mFeeder project. Stable weight detection test.\033[0m')
        # Калибровка и старт
        lib._calibrate_or_start()
        arduino = lib.start_obj()
        sleep(1)  # даём время Arduino прогреться и установить связь

        # создаём детектор и внешний цикл сбора
        detector = create_stable_weight_detector(
            presence_thr=PRESENCE_THRESHOLD,
            stability_thr=STABILITY_THRESHOLD,
            stable_duration=STABLE_DURATION,
            window_size=WINDOW_SIZE
        )

        weight_arr = []
        while True:
            w = arduino.get_measure_2()
            logger.info(f"Current weight: {w:.2f} kg")
            stable_w = detector(w)
            if stable_w is not None:
                weight_arr.append(stable_w)
                break
            time.sleep(0.1)

        # пример использования: вывести весь массив стабильных замеров
        logger.info(f"All detected stable weights: {weight_arr}")

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
