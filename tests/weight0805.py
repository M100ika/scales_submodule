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
    """
    Возвращает функцию detector(w), которую нужно вызывать для каждого нового замера w.
    detector возвращает None, пока вес не установится,
    и как только на протяжении stable_duration подряд все замеры
    попадают в [медиана окна ± stability_thr], отдаёт медиану этих замеров.
    """
    window_buf = deque(maxlen=window_size)
    valid_readings = []
    stable_start = None

    def detector(w: float) -> Optional[float]:
        nonlocal stable_start
        window_buf.append(w)
        med = statistics.median(window_buf)

        # если мы ещё не «увидели» животных (медиана окна < presence_thr),
        # сбрасываем всё и ждём
        if med < presence_thr:
            stable_start = None
            valid_readings.clear()
            return None

        # отфильтровываем выбросы относительно медианы окна
        if abs(w - med) <= stability_thr:
            # при первом попавшемся «правильном» замере запускаем таймер
            if stable_start is None:
                stable_start = time.time()
            valid_readings.append(w)
        else:
            # обнаружился выброс — сбрасываем всю историю и таймер
            stable_start = None
            valid_readings.clear()
            return None

        # проверяем, не прошло ли уже время стабильности
        if time.time() - stable_start >= stable_duration:
            # возвращаем медиану накопленных «правильных» показаний
            return statistics.median(valid_readings)

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
            stable = detector(w)
            if stable is not None:
                logger.info(f"Stable weight detected: {stable:.2f} kg")
                weight_arr.append(stable)
                break
            sleep(0.1)

        logger.info(f"All stable readings: {weight_arr}")

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
