#!/usr/bin/env python3
import sys
import time
from pathlib import Path
from loguru import logger

import statistics
from collections import deque
from pathlib import Path
from loguru import logger
from time import sleep

# Добавляем src в PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parent.parent / 'src'))

from _config_manager import ConfigManager
import _lib_pcf as lib
from _adc_data import ArduinoSerial  # именно этот класс
# from _chafon_rfid_lib import RFIDReader  # не нужен здесь

PRESENCE_THRESHOLD = 20.0    # кг — начало/конец взвешивания
WINDOW_SIZE       = 10       # размер скользящего окна для медианы
READ_PERIOD       = 0.1 

config_manager = ConfigManager()


def calibrate(
    scale_dev: ArduinoSerial,
    cfg: ConfigManager,
    timeout: float = 120.0,
    samples_zero: int = 20,
    samples_span: int = 20
):
    """
    Калибровка по двум шагам:
      1) Смещение (offset)
      2) Чувствительность (scale)
    """
    deadline = time.time() + timeout

    try:
        scale_dev.connect()

        # === Шаг 1: Offset ===
        logger.info("=== Шаг 1: калибровка нуля ===")
        logger.info("Убедитесь, что платформа пуста и нажмите Enter")
        lib.__input_with_timeout(
            deadline - time.time()
        )
        raw_zero = scale_dev.calib_read_average(samples_zero)
        scale_dev.set_offset(raw_zero)
        logger.info(f"raw_zero = {raw_zero:.2f}")

        # === Шаг 2: Span ===
        logger.info("=== Шаг 2: калибровка чувствительности ===")
        logger.info("Положите эталонный груз на платформу и нажмите Enter")
        lib.__input_with_timeout(
            deadline - time.time()
        )

        raw_with_weight = scale_dev.calib_read_average(samples_span)
        delta = raw_with_weight - scale_dev.get_offset()
        logger.info(f"raw_with_weight = {raw_with_weight:.2f}, Δ = {delta:.2f}")

        if delta <= 0:
            raise RuntimeError("Ошибка span: Δ должно быть > 0. Проверьте подключение и массу.")

        logger.info("Введите массу эталонного груза в кг (например, 20):")
        weight_str = lib.__input_with_timeout(
            deadline - time.time()
        )
        try:
            weight_kg = float(weight_str)
            if weight_kg <= 0:
                raise ValueError
        except ValueError:
            raise ValueError("Неверный ввод массы, ожидается положительное число.")

        scale_factor = delta / weight_kg
        scale_dev.set_scale(scale_factor)
        logger.info(f"scale_factor = {scale_factor:.6f} raw/кг")

        # === Сохранение в конфиг ===
        # В конфиг пишем именно числовые строки, без предварительного форматирования
        cfg.update_setting("Calibration", "Offset", raw_zero)
        cfg.update_setting("Calibration", "Scale",  scale_factor)

        logger.success("Калибровка успешно завершена")
        logger.info(f"Итоги: offset={raw_zero:.2f}, scale={scale_factor:.6f}")

    except TimeoutError:
        logger.error("Калибровка прервана по таймауту ввода")
    except Exception as e:
        logger.exception(f"Ошибка во время калибровки: {e}")
    finally:
        scale_dev.disconnect()


def main():
    # Получаем объект для работы с HX711
    try:
        input("Для начала введите 'y' и нажмите Enter")
        if input() == 'y':
            logger.info("Старт калибровки")
            arduino = lib.start_obj()
            if not isinstance(arduino, ArduinoSerial):
                logger.error("start_obj() вернул не тот тип устройства для калибровки")
            logger.info("Старт калибровки сумматора")
            calibrate(arduino, config_manager)          
        
        arduino = lib.start_obj()
        window_buf = deque(maxlen=WINDOW_SIZE)
        weight_arr = []
        collecting = False
        logger.info("Ожидаем, пока корова встанет на весы...")

        while True:
            # 3) Снимаем показание
            w = arduino.get_measure_2()
            window_buf.append(w)
            med = statistics.median(window_buf)
            logger.debug(f"Текущий raw: {w:.2f} кг, медиана окна: {med:.2f} кг")

            if not collecting:
                # ждём прихода коровы
                if med >= PRESENCE_THRESHOLD:
                    collecting = True
                    weight_arr.clear()
                    logger.info("Корова встала — начинаем сбор данных.")
            else:
                # корова на весах — собираем
                if med >= PRESENCE_THRESHOLD:
                    weight_arr.append(w)
                    logger.debug(f"  Собираем: {w:.2f} кг")
                else:
                    # корова съехала — завершаем
                    final_weight = statistics.median(weight_arr) if weight_arr else 0.0
                    logger.info(f"Корова ушла — итоговый вес: {final_weight:.2f} кг")
                    break

            sleep(READ_PERIOD)

        # 4) Дальнейшая обработка
        # здесь можно, например, отправить final_weight на сервер
        # или сохранить весь массив weight_arr
        logger.info(f"Собранные замеры ({len(weight_arr)}): {weight_arr}")

    except KeyboardInterrupt:
        logger.info("Калибровка прервана пользователем")
    except Exception as e:
        logger.exception(f"Ошибка во время калибровки: {e}")
    finally:
        arduino.disconnect()
        logger.info("Отключение от устройства")
        logger.info("Сохранение конфигурации")
    logger.info("Выход из скрипта калибровки")


if __name__ == "__main__":
    main()
