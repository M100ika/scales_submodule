#!/bin/bash
# Git pull и перезагрука
# Перейти в нужную директорию
cd /home/pi/scales7.1/scales_submodule/

# Выполнить git pull
git pull

# Перезагрузить систему
sudo reboot 


#Чтобы установить сделайте следующее 
#crontab -e
#Добавьте строку в cron 
#0 4 * * * /home/pi/scales7.1/scales_submodule/services/update_and_reboot.sh >> /home/pi/scales7.1/scales_submodule/services/update_and_reboot.log 2>&1
