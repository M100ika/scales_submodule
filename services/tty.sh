#!/bin/bash
RULES=/etc/udev/rules.d/99-usb-serial.rules
sudo touch "$RULES"

L1='SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", SYMLINK+="ttyCH340"'
L2='SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="ttyCP210x"'
L3='SUBSYSTEM=="tty", ATTRS{idVendor}=="2341", ATTRS{idProduct}=="0043", SYMLINK+="ttyArduinoUno"'

grep -qF "$L1" "$RULES" || echo "$L1" | sudo tee -a "$RULES" >/dev/null
grep -qF "$L2" "$RULES" || echo "$L2" | sudo tee -a "$RULES" >/dev/null
grep -qF "$L3" "$RULES" || echo "$L3" | sudo tee -a "$RULES" >/dev/null

sudo udevadm control --reload-rules
sudo udevadm trigger
