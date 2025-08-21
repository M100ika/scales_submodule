#!/bin/bash
echo 'SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", SYMLINK+="ttyCH340"' | sudo tee /etc/udev/rules.d/99-usb-serial.rules
echo 'SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="ttyCP210x"' | sudo tee -a /etc/udev/rules.d/99-usb-serial.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
