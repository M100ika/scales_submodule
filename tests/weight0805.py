import sys
import time
import statistics
from collections import deque
from pathlib import Path
from loguru import logger
from time import sleep

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


def wait_for_stable_weight(
    arduino,
    presence_thr: float,
    stability_thr: float,
    stable_duration: float,
    window_size: int = WINDOW_SIZE
) -> float:
    """
    Ждёт пока:
     1) вес > presence_thr
     2) в течение stable_duration подряд все отфильтрованные показания не выходят
        за рамки stability_thr от медианы скользящего окна
    Возвращает медиану списка отфильтрованных valid_readings.
    """
    window_buf = deque(maxlen=window_size)
    valid_readings = []
    stable_start = None

    logger.debug("Ожидание животного на весах...")
    while True:
        w = arduino.get_measure_2()  # кг
        window_buf.append(w)

        # фильтруем выброс
        med = statistics.median(window_buf)
        if abs(w - med) <= stability_thr:
            valid_readings.append(w)
            logger.debug(f"  Принято: {w:.2f} (медиана окна {med:.2f})")
        else:
            logger.debug(f"  Отклонение: {w:.2f} — выброс, игнорируется")

        # проверяем наличие животного
        if med >= presence_thr:
            if stable_start is None:
                stable_start = time.time()
                logger.debug("  Порог присутствия достигнут, запускаем таймер стабильности")
            elif time.time() - stable_start >= stable_duration:
                # Всё время было стабильно
                result = statistics.median(valid_readings)
                logger.debug(f"  Стабильность достигнута ({stable_duration}s), выдаём {result:.2f} kg")
                return result
        else:
            # животного нет — сбрасываем
            if stable_start is not None:
                logger.debug("  Вес опустился ниже порога, сброс таймера стабильности")
            stable_start = None
            valid_readings.clear()

        sleep(0.1)


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
            stable_w = wait_for_stable_weight(
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
