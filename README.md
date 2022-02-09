# proxmox-backup-check
 Возникла необходимость проверки, что существуют бекапы VM на PBS не старше определенного времени. 

Скрипт подключается к ноде по Proxmox VE API через https. 

Для работы скрипта должен быть установлен pip.

# Как пользоватся:

1. Указать IP, имя пользователя и пароль для подключения к любой ноде кластера на строке 34:

```bash
proxmox = ProxmoxAPI("xxx.xxx.xxx.xxx", user="user@pam", password="xxxxxxxxxxxxxx", verify_ssl=False)
```

2) Проверит акруальность бекапов за 48ч:

```bash
python3 proxmox-backup-check.py
```

3) Проверит акруальность бекапов за произвольное количество часов:

```bash
python3 proxmox-backup-check.py -t <difference in hours>
```
