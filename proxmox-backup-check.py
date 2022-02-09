import sys, time

try:
    import requests
except ModuleNotFoundError:
    import pip
    pip.main(['install', "requests"]) 
    import requests

try:
    from proxmoxer import ProxmoxAPI
except ModuleNotFoundError:
    import pip
    pip.main(['install', "proxmoxer"]) 
    from proxmoxer import ProxmoxAPI

try:
    import json
except ModuleNotFoundError:
    import pip
    pip.main(['install', "json"]) 
    import json

def p_red(text):
    return("\033[31m"+text+"\033[0m")

def p_yellow(text):
    return("\033[33m"+text+"\033[0m")

def p_green(text):
    return("\033[32m"+text+"\033[0m")

# Параметры подключения
proxmox = ProxmoxAPI("xxx.xxx.xxx.xxx", user="root@pam", password="xxxxxxxxxxxxxx", verify_ssl=False)

# Определение переменных
nodes = []
storages = []
storage = {}
# Время по умолчанию 48ч
h = 172800 
# Проверка входных аргументов
if len(sys.argv) > 2:
    if (sys.argv[1] == "-t"):
        try:
            h = 3600 * int(sys.argv[2])
        except ValueError:
            sys.exit('Use proxmox-backup-check.py -t <difference in hours>')

# Получаем список нод
for node in proxmox.nodes.get():
    nodes.append(node['node'])

# Получаем список стораджей
storages = proxmox.storage.get()

# Оставляем сторадж с type = pbs
for stor in storages:
    if stor['type'] == 'pbs':
        storage = stor

# Запрашиваем список бекапов
backups = proxmox.nodes(nodes[0]).storage(storage['storage']).content.get()

# Отсеиваем лишнее
backups_short = []
for i in range(len(backups)):
    if (time.time() - backups[i]['ctime']) < h:
        backups_short.append(backups[i])


# Проверка актуальности бекапов:
vms_status =[]
for node in nodes:
    bad_vm = []
    good_vm =[]
    #print("\033[33m{}\033[0m".format(node + ':'))
    for vm in proxmox.nodes(node).qemu.get():
        if vm['vmid'] not in bad_vm:
            bad_vm.append(vm['vmid'])
        for backup in backups_short:
            if backup['vmid'] == vm['vmid']:
                bad_vm.remove(vm['vmid'])
                good_vm.append(vm['vmid'])
                break
    vms_status.append({'name': node, 'bad_vm': bad_vm, 'good_vm': good_vm})

# Вывод результатов
for mv_status in vms_status:
    print(p_yellow(mv_status['name']+':'))
    for vmid in mv_status['good_vm']:
        print(str(vmid) + ' | ' + p_green('backup OK'))
    for vmid in mv_status['bad_vm']:
        print(p_red(str(vmid)) + ' | ' + p_red('NO backup'))
