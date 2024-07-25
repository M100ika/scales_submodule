#!/bin/bash

# Проверка наличия прав суперпользователя
if [ "$(id -u)" -ne 0 ]; then
    echo "Этот скрипт нужно запускать с правами суперпользователя (root)." >&2
    exit 1
fi

# Включаем systemd-networkd
systemctl enable systemd-networkd
systemctl start systemd-networkd

# Создаем конфигурационный файл для eth0
cat > /etc/systemd/network/10-eth0.network <<EOF
[Match]
Name=eth0

[Network]
Address=192.168.1.249/24
Gateway=192.168.1.1
DNS=192.168.1.1 8.8.8.8 fd51:42f8:caae:d92::1
EOF

# Перезапускаем systemd-networkd для применения изменений
systemctl restart systemd-networkd

echo "Настройка сетевого интерфейса eth0 завершена."