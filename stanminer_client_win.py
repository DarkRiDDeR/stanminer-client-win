import argparse
import subprocess
import socket
import time
import os
import sys
import zipfile
import platform
import json
import re
import configparser
import hashlib
import base64
import logging

_g_version = "0.1.1a"
_g_config = [] # config.ini
_g_tauko = 20
_g_miners = {
    'binaryexpr': {
        'version': '0.6.26',
        'url': 'https://github.com/BinaryExpr/spectre-miner/releases/download/v0.6.26/spectre_miner_x64-v0.6.26_windows.zip',
        'subfolder': '',
        'exe': 'spectre-miner'
    },
    'cpuminer-opt-rplant': {
        'version': '5.0.41',
        'url': 'https://github.com/rplant8/cpuminer-opt-rplant/releases/download/5.0.41/cpuminer-opt-win-5.0.41.zip',
        'subfolder': '',
        'exe': 'cpuminer-sse2'
    },
    'hellminer': {
        'version': '0.59.1',
        'url': 'https://github.com/hellcatz/hminer/releases/download/v0.59.1/hellminer_win64_avx2.zip',
        'subfolder': '',
        'exe': 'hellminer'
    },
    'tnn-miner': {
        'version': '0.4.4-r2',
        'url': 'https://gitlab.com/Tritonn204/tnn-miner/-/releases/0.4.4-r2/downloads/Tnn-miner-win64-0.4.4-r2.zip',
        'subfolder': '',
        'exe': 'tnn-miner-cpu'
    },
    'srbminer-multi': {
        'version': '2.6.9',
        'url': 'https://github.com/doktor83/SRBMiner-Multi/releases/download/2.6.9/SRBMiner-Multi-2-6-9-win64.zip',
        'subfolder': 'SRBMiner-Multi-2-6-9',
        'exe': 'SRBMiner-MULTI'
    },
    'xmrig': {
        'version': '6.22.1',
        'url': 'https://github.com/xmrig/xmrig/releases/download/v6.22.1/xmrig-6.22.1-gcc-win64.zip',
        'subfolder': 'xmrig-6.22.1',
        'exe': 'xmrig'
    },
}

# ANSI-code colors 
YELLOW = "\033[93m"
RESET = "\033[0m"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    #format='%(asctime)s - %(levelname)s - %(message)s',
    format='%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

    
class ReconnectException(Exception):
    pass

# Проверяем, установлен ли модуль requests
try:
    import requests
except ImportError:
    logger.info("The requests module is not installed. Installing...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
        import requests
        logger.info("The requests module has been installed successfully")
    except subprocess.CalledProcessError:
        logger.error(f"Error installing requests module.")
        
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
        logger.warning(f"An error occurred: {e}")
        return []
    
'''
No response from server.
Command not received. Retrying in 20 seconds...
Starting new HTTP connection (1): 127.0.0.1:8085
http://127.0.0.1:8085 "GET /data.json HTTP/11" 200 3637
Send request to server ('stanvps.ddns.net', 8101):
{'wallet': 'UQCFVXtlCUjTY5n1zdwXbALgsbYQK1WrZUfAzU3shSyMx5D8', 'worker': 'm2670WIN', 'threads': 48, 'command_hash': 'NONE', 'temps': [{'cpu': 38, 'temps': []}, {'cpu': 38, 'temps': []}], 'hashrate_value': '', 'hashrate_unit': ''}


No response from server.
Command not received. Retrying in 20 seconds...
'''
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
            _g_config.set('MAIN', 'port', '8101')
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
        logger.error(f"An error occurred: {e}")
        sys.exit(1)

def start_load_miners():
    try:
        dir = "./"

        for minerName, miner in _g_miners.items():
            dirMiner = os.path.join(dir, minerName + '/' + miner['version'] + '/')
            fileName = os.path.basename(miner['url'])
            if not os.path.exists(dirMiner):
                if not os.path.exists(fileName):
                    logger.info("Download miner " + minerName + " " + miner['version'])
                    powershell(f"Invoke-RestMethod -Uri '{miner['url']}' -OutFile '{fileName}'")
                with zipfile.ZipFile(fileName,"r") as zip_ref:
                    zip_ref.extractall(dirMiner)
                os.remove(fileName)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)

def stop_mining():
    try:
        processes = []
        for miner in _g_miners.values():
            processes.append(f"'{miner['exe']}'")
        powershell("Get-Process -Name " + ",".join(processes) + " | Stop-Process -Force")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return
    

''' FROM SERVER

rm -rf /tmp/STAN_MINER/CURRENT_MINER;
mkdir -p /tmp/STAN_MINER/CURRENT_MINER;
cd /tmp/STAN_MINER/CURRENT_MINER && wget https://stanvps.ddns.net/dev-docs/tnn-miner-super.tar.gz && tar -xzf tnn-miner-super.tar.gz;
/tmp/STAN_MINER/CURRENT_MINER/tnn-miner --dev-fee 1 --daemon-address 93.100.220.206 --port 8114 --wallet STAN_WALLET --worker-name STAN_WORKER --threads STAN_THREADS

rm -rf /tmp/STAN_MINER/CURRENT_MINER;
mkdir -p /tmp/STAN_MINER/CURRENT_MINER;
cd /tmp/STAN_MINER/CURRENT_MINER && wget https://github.com/xmrig/xmrig/releases/download/v6.21.3/xmrig-6.21.3-linux-static-x64.tar.gz && tar -xzf xmrig-6.21.3-linux-static-x64.tar.gz;
/tmp/STAN_MINER/CURRENT_MINER/xmrig-6.21.3/xmrig --algo rx/wow -o 93.100.220.206:8112 -u STAN_WALLET.STAN_WORKER -t STAN_THREADS --randomx-1gb-pages

rm -rf /tmp/STAN_MINER/CURRENT_MINER; mkdir -p /tmp/STAN_MINER/CURRENT_MINER;
cd /tmp/STAN_MINER/CURRENT_MINER && wget https://github.com/hellcatz/hminer/releases/download/v0.59.1/hellminer_linux64.tar.gz && tar -xzf hellminer_linux64.tar.gz;
/tmp/STAN_MINER/CURRENT_MINER/hellminer -c stratum+tcp://93.100.220.206:8115 -u STAN_WALLET.STAN_WORKER -p d=16384S --cpu=STAN_THREADS

    )
'''

def start_mining(miner, args):
    if miner in _g_miners:
        dir = os.path.join(miner, _g_miners[miner]['version'], _g_miners[miner]['subfolder'])
        args = args.replace("'", "''")
        cmd = f"Start-Process -FilePath '{_g_miners[miner]['exe']}.exe' -WorkingDirectory '{dir}' -ArgumentList '{args}'"
        logger.info(cmd)
        if _g_config.getboolean('MAIN', 'hide_mining_window'):
            cmd += ' -WindowStyle hidden'
        powershell(cmd)
    else:
        raise Exception(f'Miner "{miner}" not find')

def send_parameters_and_get_command(server, wallet, worker, threads, command_hash):
    global _g_config, _g_version

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect(server)
            client_socket.settimeout(10)

            fileobj = client_socket.makefile('rw')
            temps = []
            if (_g_config.getboolean('MAIN', 'detect_temperature')):
                temps = get_cpu_temperature()
            #logger.debug(f"STAN INFO: {worker} temperatures: {temps}") 

            # Prepare request
            request = {
                'wallet': wallet,
                'worker': worker,
                'threads': threads,
                'command_hash': command_hash,
                'temps': temps,
                'hashrate_value': 0,
                'hashrate_unit': 0,
                'platform': 'Windows client ' + _g_version
            }
            logger.debug(f"Send request to server {server}:\n{request}\n\n") # {command}

            # Send request
            fileobj.write(json.dumps(request) + '\n')
            fileobj.flush()
            #logger.info(f"Sent request to server: {request}")

            # Read response
            response_line = fileobj.readline()
            if not response_line:
                logger.warning("No response from server.")
                return None

            response = json.loads(response_line.strip())
            #logger.debug(f"Received response from server: {response}")

            if response.get('status') == 'NO_CHANGE':
                #logger.info("No change in command from server.")
                return None
            elif response.get('status') == 'NEW_COMMAND':
                command = response.get('command')
                logger.debug(f"Received new command from server: {command}")
                return command
            else:
                logger.warning(f"Unknown response from server: {response}")
                return None
    except Exception as e:
        #logger.error(f"Error communicating with server {server_address}: {e}")
        return None      

def main_loop(server, user_wallet, worker, user_threads):
    global _g_config
    command = None
    command_hash = None
    prev_command_hash = "NONE"
    logging.info('Temperature detection: ' + ('enable' if _g_config.getboolean('MAIN', 'detect_temperature') else 'disable'))

    while True:
        command = send_parameters_and_get_command(server, user_wallet, worker, user_threads, prev_command_hash)

        if command is not None:
            command_hash = hashlib.sha256(command.encode('utf-8')).hexdigest()
            logger.info("STAN-START is active")

            while True:
                try:
                    if prev_command_hash != command_hash:
                        logger.info("New command received.")
                        prev_command_hash = command_hash if command_hash else "NONE"
                        stop_mining()

                        if "cpuminer-opt-rplant" in command:
                            start_mining("cpuminer-opt-rplant", re.sub(r'^.*/cpuminer-sse2 (.*)$', r'\1', command, flags=re.S))
                        elif "/tmp/STAN_MINER/CURRENT_MINER/SRBMiner-Multi" in command:
                            start_mining("srbminer-multi", re.sub(r'^.*/SRBMiner-MULTI (.*?)$', r'\1', command, flags=re.S))
                        elif "/tmp/STAN_MINER/CURRENT_MINER/xmrig" in command:
                            start_mining("xmrig", re.sub(r'^.*/xmrig (.*?)$', r'\1', command, flags=re.S))
                        elif "/tmp/STAN_MINER/CURRENT_MINER/spectre" in command:
                            start_mining("binaryexpr", re.sub(r'^.*/spectre-miner (.*?)$', r'\1', command, flags=re.S))
                        elif "/tmp/STAN_MINER/CURRENT_MINER/tnn-miner" in command:
                            start_mining("tnn-miner", re.sub(r'^.*/tnn-miner (.*?)$', r'\1', command, flags=re.S))
                        elif "/tmp/STAN_MINER/CURRENT_MINER/hellminer" in command:
                            start_mining("hellminer", re.sub(r'^.*/hellminer (.*?)$', r'\1', command, flags=re.S))
                        elif "/tmp/STAN_MINER/CURRENT_MINER/" in command: # most likely some unknown miner
                            logger.error("Most likely some unknown miner for the client. Mining stopped")
                            logger.error("Server command:\n------\n" + command)
                            break
                        else:
                            logger.error("When parsing commands from the server, the miner was not found\n")
                            logger.error("Server command:\n------\n" + command)
                            break

                    time.sleep(180)
                    command = send_parameters_and_get_command(server, user_wallet, worker, user_threads, prev_command_hash)

                    if command is not None:
                        command_hash = hashlib.sha256(command.encode('utf-8')).hexdigest()
                except Exception as e:
                    logger.error(f"Error sending system parameters: {e}")
                    break

        else:
            logger.info(f"Command not received. Retrying in {_g_tauko} seconds...")
            time.sleep(_g_tauko)
                

if __name__ == "__main__":  
    stop_mining() 
    configIni()
    start_load_miners()

    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--user_wallet", type=str, help="User wallet for mining", required=True)
    parser.add_argument("-t", "--user_threads", type=int, help="CPU threads for mining", required=True)
    parser.add_argument("-s", "--server", type=str, help="Server for mining", required=False, default=_g_config['MAIN']['server'])
    parser.add_argument("-p", "--port", type=int, help="Server port for mining", required=False, default=_g_config.getint('MAIN', 'port'))
    parser.add_argument("-w", "--worker", type=str, help="Worker name", required=False, default=_g_config['MAIN']['worker'])
    args = parser.parse_args()
              
    main_loop((args.server, args.port), args.user_wallet, args.worker, args.user_threads)

    logger.info("Client stopped.")