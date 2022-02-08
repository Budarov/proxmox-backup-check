import sys, os.path

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

# Параметры подключения
proxmox = ProxmoxAPI("xxx.xxx.xxx.xxx", user="root@pam", password="xxxxxxxxxxxxxx", verify_ssl=False)

# Определение переменных
work_mod = 'read'
file ='startonboot.conf'
nodes = []
st_on_boot_conf = []

# Проверка входных аргументов
if len(sys.argv) > 1:
    if sys.argv[1] == "-export":
        work_mod = 'export'
    elif sys.argv[1] == "-disable":
        work_mod = 'disable'
    elif sys.argv[1] == "-import":
        if len(sys.argv) < 3:
            sys.exit("Use -import <file.conf>")
        else:
          work_mod = 'import'

if len(sys.argv) == 3:
    file = str(sys.argv[2])

# Функция записи конфигурации в файл
def to_file(config, file):
  json_start_conf = json.dumps(config)
  with open(file,'w') as out:
    out.write(json_start_conf)
  out.close()

# Функция чтения из файла
def from_file(file):
  with open(file,'r') as conf_file:
    data = json.load(conf_file)
  conf_file.close()
  # Приведение типа VM id к int
  for i in range(len(data)):
      result = {}
      for k, v in data[i]['vm'].items():
          result[int(k)] = v
      data[i]['vm'] = result
  #--------------------------   
  return(data)

# Проверяем наличие файла
if (os.path.exists(file) == True) and ((work_mod == 'export') or (work_mod == 'disable')):
    sys.exit("\033[31m{0} \033[33m{1} \033[31m{2} \033[0m" .format('!!!!!!!! Error: File', file, 'is exist. Specify another file.'))
elif (os.path.exists(file) == False) and (work_mod == 'import'):
    sys.exit("\033[31m{0} \033[33m{1} \033[31m{2} \033[0m" .format('!!!!!!!! Error: File', file, 'is not exist. Specify an existing file.'))

# Получаем список нод
for node in proxmox.nodes.get():
    nodes.append(node['node'])

# Опрос о автостарте VM на нодах и отключение, если запрошено
for node in nodes:
    start_conf = {}
    print("\033[33m{}\033[0m".format(node + ' current state:'))
    for vm in proxmox.nodes(node).qemu.get():
        config = proxmox.nodes(node).qemu(vm['vmid']).config.get()
        if ('onboot' in config) and (config['onboot'] == 1):
          print ("{0} | {1} | Start at boot = \033[32m{2} \033[0m" .format(vm['vmid'], vm['name'], config['onboot']))
          start_conf[vm['vmid']] = config['onboot']
          if work_mod == 'disable':
              print (" \033[31m{0} | {1} | Start at boot \033[32m{2} \033[31m{3} \033[0m" .format(vm['vmid'], vm['name'], config['onboot'], '=> 0'))
              proxmox.nodes(node).qemu(vm['vmid']).config.put(onboot=0)

        else:
          config['onboot'] = 0
          print ("{0} | {1} | Start at boot = \033[31m{2} \033[0m" .format(vm['vmid'], vm['name'], config['onboot']))
          start_conf[vm['vmid']] = config['onboot']
    st_on_boot_conf.append({'name':node, 'vm':start_conf})

# Записываем в файл
if work_mod == 'export' or work_mod == 'disable':
  to_file(st_on_boot_conf, file)

# Применение параметров из файла
if work_mod == 'import':
    new_start_conf = from_file(file)
    print(new_start_conf)
    # Проверка наличия нод из файла в кластере
    for i in range(len(nodes)):
        if new_start_conf[i]['name'] not in nodes:
            sys.exit("\033[31m{0} \033[33m{1} \033[31m{2} \033[0m" .format('!!!!!!!! Error: No node', new_start_conf[i]['name'], 'in file!!!!!!!!!'))
    # Прменяем на кластере
    for node in new_start_conf:
        print("\033[33m{0} \033[31m{1}\033[0m".format(node['name'], 'changing autostart state:'))
        for vm in proxmox.nodes(node['name']).qemu.get():
            # Проверка наличия VM id в файле
            if vm['vmid'] not in node['vm']:
                sys.exit("\033[31m{0} \033[33m{1} \033[31m{2} \033[33m{3} \033[0m" .format('!!!!!!!! Error: No VM id', vm['vmid'], 'from file on node', node['name']))    
            print("VM \033[32m{0}\033[0m to \033[31m{1} \033[0m" .format(str(vm['vmid']), str(node['vm'][vm['vmid']])))
            proxmox.nodes(node['name']).qemu(vm['vmid']).config.put(onboot=node['vm'][vm['vmid']])

