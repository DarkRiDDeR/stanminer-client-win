import argparse
import subprocess
import socket
import time
import os
import signal
import sys
import zipfile
import urllib.request
import platform
import json
import re
import configparser
import hashlib
import base64

_g_version = "1.03"
_g_config = [] # config.ini
_g_miners = {
    'cpuminer-opt-rplant': {
        'version': '5.0.40',
        'url': 'https://github.com/rplant8/cpuminer-opt-rplant/releases/download/5.0.40/cpuminer-opt-win-5.0.40.zip',
        'subfolder': '',
        'exe': 'cpuminer-sse2'
    },
    'srbminer-multi': {
        'version': '2.5.7',
        'url': 'https://github.com/doktor83/SRBMiner-Multi/releases/download/2.5.7/SRBMiner-Multi-2-5-7-win64.zip',
        'subfolder': 'SRBMiner-Multi-2-5-7',
        'exe': 'SRBMiner-MULTI'
    },
    'xmrig': {
        'version': '6.21.3',
        'url': 'https://github.com/xmrig/xmrig/releases/download/v6.21.3/xmrig-6.21.3-gcc-win64.zip',
        'subfolder': 'xmrig-6.21.3',
        'exe': 'xmrig'
    },
    'spectre': {
        'version': '0.6.20',
        'url': ' https://github.com/BinaryExpr/spectre-miner/releases/download/v0.6.20/spectre_miner_x64-v0.6.20_windows.zip',
        'subfolder': '',
        'exe': 'spectre-miner'
       
    }
}

    
class ReconnectException(Exception):
    pass

# Проверяем, установлен ли модуль requests
try:
    import requests
except ImportError:
    print("The requests module is not installed. Installing...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
        print("The requests module has been installed successfully.")
    except subprocess.CalledProcessError:
        print("Error installing requests module.")
        sys.exit(1)
        
def format_list_temp_line(line):
    parts = line.split(':', 2)
    if len(parts) == 2:
        label = parts[0].strip()
        temp_value = parts[1].strip().split()[0].replace('°c', '').replace('+', '')
        temp_value = int(float(temp_value))
        return [label, temp_value]
    return None


def get_cpu_temperature():
    try:
        temps = []
        d = requests.get('http://' + _g_config['MAIN']['libre_hardware_monitor'] + '/data.json')
        d = d.json()
        re_pattern_temper = r'^.*?([\d]+).*$'
        for device in d['Children'][0]['Children']:
            if re.search(r'^(Intel|AMD)\s', device['Text'], flags=re.IGNORECASE):
                for group in device['Children']:
                    if group['Text'] == 'Temperatures':
                        for temper in group['Children']:
                            if temper['Text'] == 'CPU Package':
                                t = re.sub(re_pattern_temper, r'\1', temper['Value'])
                                t = int(t) if t.isdigit() else None
                                temps.append({'cpu': t,'temps': []})
        return temps

    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    

def gen_hash_sha1_to_base64 (id):
    hash = hashlib.sha1(str(id).encode("UTF-8")) 
    return base64.b64encode(hash.digest()).decode("UTF-8", "ignore") 


def powershell(cmd, onlyStdoutResult = False):
    res = subprocess.run(["powershell", "-Command", cmd], capture_output=True, encoding = 'utf-8')
    if onlyStdoutResult:
        res = res.stdout.strip()
    return res

def configIni():
    global _g_config
    try:
        _g_config = configparser.ConfigParser()
        if not os.path.exists("config.ini"):
            _g_config.add_section('MAIN')
            _g_config.set('MAIN', 'server', 'stanvps.ddns.net')
            _g_config.set('MAIN', 'port', '8084')
            # generate hash of hostname + MAC
            hostname = powershell("hostname", True)
            mac = powershell("Get-NetAdapter | Select-Object -expandproperty MacAddress", True)
            _g_config.set('MAIN', "; worker", "hash of hostname + MAC")
            _g_config.set('MAIN', 'worker', gen_hash_sha1_to_base64(hostname + mac).replace('+', '').replace('/', '')[0:10])
            _g_config.set('MAIN', 'hide_mining_window', 'false')
            _g_config.set('MAIN', 'detect_temperature', 'false')
            _g_config.set('MAIN', 'libre_hardware_monitor', '127.0.0.1:8085')
            with open('config.ini', 'w') as configfile:
                _g_config.write(configfile)
        else:
            _g_config.read('config.ini')
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

def start_load_miners():
    try:
        dir = "./"

        for minerName, miner in _g_miners.items():
            dirMiner = os.path.join(dir, minerName + '/' + miner['version'] + '/')
            fileName = os.path.basename(miner['url'])
            if not os.path.exists(dirMiner):
                if not os.path.exists(fileName):
                    print("Download miner " + minerName + " " + miner['version'])
                    powershell(f"Invoke-RestMethod -Uri '{miner['url']}' -OutFile '{fileName}'")
                with zipfile.ZipFile(fileName,"r") as zip_ref:
                    zip_ref.extractall(dirMiner)
                os.remove(fileName)

    except subprocess.CalledProcessError:
        print("Failed to restart screen and load. Exiting...")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)

def stop_mining():
    try:
        processes = []
        for miner in _g_miners.values():
            processes.append(f"'{miner['exe']}'")
        powershell("Get-Process -Name " + ",".join(processes) + " | Stop-Process -Force")
    except Exception as e:
        print(f"An error occurred: {e}")
        return
    

''' FROM SERVER

if miner_type == "cpuminer":
    command_download_and_run = (
        "if [ ! -d /tmp/STAN_MINER/cpuminer-opt-linux ] || [ ! -f /tmp/STAN_MINER/cpuminer-opt-linux/cpuminer-sse2 ]; then "
        "mkdir -p /tmp/STAN_MINER && "
        "cd /tmp/STAN_MINER && "
        "wget https://github.com/rplant8/cpuminer-opt-rplant/releases/download/5.0.40/cpuminer-opt-linux-5.0.40.tar.gz && "
        "tar -xzf cpuminer-opt-linux-5.0.40.tar.gz; fi && "
        "sudo /tmp/STAN_MINER/cpuminer-opt-linux-5.0.40/cpuminer-sse2 "
        "--algo " + active_algo + " -o " + active_stratum_server + " -u " + mining_address + "." + shortened_wallet + 
        " -p " + active_pass + "" + t + " 2>&1 | sudo tee /tmp/STAN_MINER/curlog > /dev/null &"
    )
elif miner_type == "srbminer":
    command_download_and_run = (
        "if [ ! -d /tmp/STAN_MINER/SRBMiner-Multi-2-5-8 ] || [ ! -f /tmp/STAN_MINER/SRBMiner-Multi-2-5-8/SRBMiner-MULTI ]; then "
        "mkdir -p /tmp/STAN_MINER && "
        "cd /tmp/STAN_MINER && "
        "wget https://github.com/doktor83/SRBMiner-Multi/releases/download/2.5.8/SRBMiner-Multi-2-5-8-Linux.tar.gz && "
        "tar -xzf SRBMiner-Multi-2-5-8-Linux.tar.gz; fi && "
        "sudo /tmp/STAN_MINER/SRBMiner-Multi-2-5-8/SRBMiner-MULTI "
        "--algorithm " + active_algo + " --pool " + active_stratum_server + " --wallet " + mining_address + "." + shortened_wallet + 
        " --password " + active_pass + "" + threads + " --keepalive true --log-file /tmp/STAN_MINER/curlog 2>&1"
    )
elif miner_type == "xmrig":
    command_download_and_run = (
        "if [ ! -d /tmp/STAN_MINER/xmrig-6.21.3 ] || [ ! -f /tmp/STAN_MINER/xmrig-6.21.3/xmrig ]; then "
        "mkdir -p /tmp/STAN_MINER && "
        "cd /tmp/STAN_MINER && "
        "wget https://github.com/xmrig/xmrig/releases/download/v6.21.3/xmrig-6.21.3-linux-static-x64.tar.gz && "
        "tar -xzf xmrig-6.21.3-linux-static-x64.tar.gz; "
        "fi; "
        "sudo /tmp/STAN_MINER/xmrig-6.21.3/xmrig "
        "--algo " + active_algo + " -o " + active_stratum_server + " -u " + mining_address + "." + shortened_wallet + 
        " -p " + active_pass + " --randomx-1gb-pages" + t + " 2>&1 | sudo tee /tmp/STAN_MINER/curlog > /dev/null & "
elif miner_type == "spectre":
    st_host, st_port = active_stratum_server.split(":")
    command_download_and_run = (
        #"sudo apt install libhwloc15 -y; " # работает инсталяция
        "if [ ! -d /tmp/STAN_MINER/spectre ] || [ ! -f /tmp/STAN_MINER/spectre/spectre-miner ]; then "
        "mkdir -p /tmp/STAN_MINER/spectre &&  "
        "cd /tmp/STAN_MINER && "
        "wget https://github.com/BinaryExpr/spectre-miner/releases/download/v0.6.20/spectre_miner_x64-v0.6.20_linux.tar.gz && "
        "tar -xzf spectre_miner_x64-v0.6.20_linux.tar.gz -C spectre; "
        "fi; "
        "sudo /tmp/STAN_MINER/spectre/spectre_miner_x64/spectre-miner "
        "-d " + active_stratum_server + " -w " + mining_address + "." + shortened_wallet +
        " " + t + " 2>&1 | sudo tee /tmp/STAN_MINER/curlog > /dev/null & "
    )
'''

def start_mining(miner, args):
    if miner in _g_miners:
        dir = os.path.join(miner, _g_miners[miner]['version'], _g_miners[miner]['subfolder'])
        cmd = f"Start-Process -FilePath '{_g_miners[miner]['exe']}.exe' -WorkingDirectory '{dir}' -ArgumentList '{args}'"
        print(cmd)
        if _g_config.getboolean('MAIN', 'hide_mining_window'):
            cmd += ' -WindowStyle hidden'
        powershell(cmd)
    else:
        raise Exception(f'Miner "{miner}" not find')
        

def receive_commands(server_host, server_port, user_wallet, user_threads):
    prev_command = ""
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            print(f"Connecting to server at {server_host}:{server_port}...")

            while True:
                try:
                    client_socket.connect((server_host, server_port))
                    #print(f"Connected to server at {server_host}:{server_port}")
                    break
                except ConnectionRefusedError:
                    print("Connection refused, retrying in 20 seconds...")
                    time.sleep(20)

            os_version = platform.system() + " " + platform.version()
            message = json.dumps({
                'new_connection': 'true', 
                'wallet': user_wallet, 
                'user_threads': user_threads,
                'hostname': _g_config['MAIN']['worker'], 
                'version': _g_version, 
                'os_version': os_version
            })
            client_socket.sendall(message.encode('utf-8'))
            #print(f"Sent data to server: {message}")

            try:
                while True:
                    # Получаем команду от сервера
                    command = client_socket.recv(4096).decode()
                    if not command:
                        print("No command received, reconnecting...")
                        raise ReconnectException

                    # Очистка экрана перед выводом сообщений
                    #os.system('clear' if os.name == 'posix' else 'cls')

                    print(f"STAN-START is starting...\n------{command}\n") # {command}
                    print("STAN-START is active.\n------\n")

                    if prev_command != command:
                        prev_command = command
                        # parse command and start mining
                        if "sudo /tmp/STAN_MINER/cpuminer-opt" in command:
                            stop_mining()
                            start_mining("cpuminer-opt-rplant", re.sub(r'^.*/cpuminer-sse2 (.*?)2>&1.*$', r'\1', command, flags=re.S))
                        elif "sudo /tmp/STAN_MINER/SRBMiner-Multi" in command:
                            stop_mining()
                            start_mining("srbminer-multi", re.sub(r'^.*/SRBMiner-MULTI (.*?)--log-file.*$', r'\1', command, flags=re.S))
                        elif "sudo /tmp/STAN_MINER/xmrig" in command:
                            stop_mining()
                            start_mining("xmrig", re.sub(r'^.*/xmrig (.*?)2>&1.*$', r'\1', command, flags=re.S))
                        elif "sudo /tmp/STAN_MINER/spectre" in command:
                            stop_mining()
                            start_mining("spectre", re.sub(r'^.*/spectre-miner (.*?)2>&1.*$', r'\1', command, flags=re.S))
                        elif "sudo /tmp/STAN_MINER/" in command: # most likely some unknown miner
                            stop_mining()
                            print("Most likely some unknown miner for the client. Mining stopped\n------\n" + command)
                        else:
                            print("When parsing commands from the server, the miner was not found\n")
                            print("Server command:\n------\n" + command)


                    while True:
                        try:
                            # Дополнительно можно отправлять информацию о состоянии системы
                            temps = []
                            if (_g_config.getboolean('MAIN', 'detect_temperature')):
                                temps = get_cpu_temperature()
                            last_10_lines = [] #read_last_10_lines(log_file_path)
                            cpu_load = None #load = get_cpu_load()
                            message = json.dumps({
                                'connected': 'true',
                                'wallet': user_wallet,
                                'hostname': _g_config['MAIN']['worker'],
                                'temps': temps,
                                'version': _g_version,
                                'last_10_lines': last_10_lines,
                                'cpu_load': cpu_load
                            })
                            client_socket.sendall(message.encode('utf-8'))
                            #print(f"MESSAGE: {message}")
                        except StopIteration:
                            break
                        except Exception as e:
                            print(f"An error occurred while reading the log file: {e}")
                            break

                        time.sleep(60)
            except (BrokenPipeError, ConnectionResetError, ReconnectException):
                print("Connection to the server lost, retrying in 5 seconds...")
                time.sleep(5)
                continue
            except Exception as e:
                print(f"An error occurred: {e}")
                break
            finally:
                print("Cleaning up and preparing to reconnect...")
                client_socket.close()
                

if __name__ == "__main__":  
    stop_mining() 
    configIni()
    start_load_miners()
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--user_wallet", type=str, help="User wallet for mining", required=True)
    parser.add_argument("-t", "--user_threads", type=str, help="CPU threads for mining", required=False)
    args = parser.parse_args()

    receive_commands(_g_config['MAIN']['server'], _g_config.getint('MAIN', 'port'), args.user_wallet, args.user_threads)