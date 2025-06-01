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
READ_PERIOD       = 0.1      # секунда между считываниями

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
        logger.info("Feeder project. Start weight collection until cow leaves.")
        lib._calibrate_or_start()
        arduino = lib.start_obj()
        sleep(1)  # даём Arduino прогреться

        window_buf = deque(maxlen=WINDOW_SIZE)
        weight_arr = []
        cow_on = False

        logger.info("Ожидаем прихода коровы на весы...")
        while True:
            w = arduino.get_measure_2()
            window_buf.append(w)
            med = statistics.median(window_buf)

            # Если коровы ещё нет
            if not cow_on:
                logger.debug(f"Current median = {med:.2f} kg (ожидаем ≥ {PRESENCE_THRESHOLD})")
                if med >= PRESENCE_THRESHOLD:
                    cow_on = True
                    logger.info("Корова встала на весы — начинаем сбор данных.")
            else:
                # Корова уже на весах — собираем каждое показание
                weight_arr.append(w)
                logger.debug(f"Collecting weight: {w:.2f} kg")

                # Проверяем, ушла ли корова
                if med < PRESENCE_THRESHOLD:
                    logger.info("Корова покинула весы — завершаем сбор.")
                    break

            sleep(READ_PERIOD)

        logger.info(f"Собрано {len(weight_arr)} замеров: {weight_arr}")

        # Здесь можно дальше обрабатывать weight_arr:
        # отправить на сервер, сохранить в файл и т.д.

    except KeyboardInterrupt:
        logger.info("Прервано пользователем.")
    except Exception as e:
        logger.error(f"Ошибка: {e}")
    finally:
        if arduino:
            logger.info("Отключаем Arduino.")
            arduino.disconnect()


if __name__ == "__main__":
    main()
