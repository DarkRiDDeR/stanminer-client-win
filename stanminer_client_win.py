import argparse
import subprocess
import threading
import socket
import time
import os
import sys
import zipfile
import signal
import shutil
import json
import re
import configparser
import hashlib
import logging

_g_version = "0.4.2-beta"
_g_config = {} # config.ini
_g_miners = {}
# Global variables
_g_process = None
_g_shutdown_event = threading.Event()
_g_hashrate = [0, ''] # [value, unit]

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
        #with open('./data.json', 'r') as file:
        #    d = json.load(file)

        re_pattern_temper = r'^.*?([\d]+).*$'
        for device in d['Children'][0]['Children']:
            if re.search(r'^(Intel|AMD)\s', device['Text'], flags=re.IGNORECASE):
                for group in device['Children']:
                    if group['Text'] == 'Temperatures':
                        firstCore=''
                        cpu=''
                        for temper in group['Children']:
                            name = temper['Text'].lower()
                            if ('tctl/tdie' in name) or ('package' in name):
                                cpu=temper['Value']
                                break
                            elif (not firstCore) and ('core' in name):
                                firstCore = temper['Value']

                        cpu = cpu if cpu else firstCore
                        cpu = re.sub(re_pattern_temper, r'\1', cpu)
                        cpu = int(cpu) if cpu.isdigit() else None
                        temps.append({'cpu': cpu,'temps': []})
        return temps
    except Exception as e:
        logger.warning(f"Temperature detection error: {e}")
        return []

def powershell(cmd, onlyStdoutResult = False):
    res = subprocess.run(["powershell", "-Command", cmd], capture_output=True, encoding = 'utf-8')
    if onlyStdoutResult:
        res = res.stdout.strip()
    return res
  
''' FROM SERVER
rm -rf /tmp/STAN_MINER/CURRENT_MINER;
mkdir -p /tmp/STAN_MINER/CURRENT_MINER;
cd /tmp/STAN_MINER/CURRENT_MINER && wget https://github.com/xmrig/xmrig/releases/download/v6.21.3/xmrig-6.21.3-linux-static-x64.tar.gz && tar -xzf xmrig-6.21.3-linux-static-x64.tar.gz;
/tmp/STAN_MINER/CURRENT_MINER/xmrig-6.21.3/xmrig --algo rx/wow -o 93.100.220.206:8112 -u STAN_WALLET.STAN_WORKER -t STAN_THREADS --randomx-1gb-pages

rm -rf /tmp/STAN_MINER/CURRENT_MINER; mkdir -p /tmp/STAN_MINER/CURRENT_MINER;
cd /tmp/STAN_MINER/CURRENT_MINER && wget https://github.com/hellcatz/hminer/releases/download/v0.59.1/hellminer_linux64.tar.gz && tar -xzf hellminer_linux64.tar.gz;
/tmp/STAN_MINER/CURRENT_MINER/hellminer -c stratum+tcp://93.100.220.206:8115 -u STAN_WALLET.STAN_WORKER -p d=16384S --cpu=STAN_THREADS
'''

def start_mining(miner, args):
    global _g_process

    if miner in _g_miners:
        dir = os.path.join(miner, _g_miners[miner]['version'])
        if 'subfolder' in _g_miners[miner]:
            dir = os.path.join(dir, _g_miners[miner]['subfolder'])
        args = args.replace("'", "''")
        cmd = os.path.abspath(os.path.join(dir, f"{_g_miners[miner]['exe']}"))
        cmd = f'"{cmd}" {args}'
        if 'args' in _g_miners[miner]:
            cmd += ' ' + _g_miners[miner]['args']
        logger.info("------\nNew command received:\n" + cmd + "\n------\n")
        env = os.environ.copy()
        env['LANG'] = 'en_US.UTF-8'
        env['LC_ALL'] = 'en_US.UTF-8'
        env['SYSTEMD_COLORS'] = '1'
        
        if miner == 'xmrig' or miner == 'cpuminer-opt-rplant': # detect hashrate
            _g_process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                env=env,
                universal_newlines=True,
                encoding='utf-8'
            )
            threading.Thread(target=read_process_output, args=(_g_process,miner), daemon=True).start()
        else:
            _g_process = subprocess.Popen(
                cmd,
                shell=True,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                env=env,
                universal_newlines=True,
                encoding='utf-8'
            )
            threading.Thread(args=(_g_process,miner), daemon=True).start()
    else:
        raise Exception(f'Miner "{miner}" not find')

def read_process_output(process, miner):
    global _g_hashrate
    try:
        for line in process.stdout:
            if isinstance(line, bytes):
                line = line.decode('utf-8', errors='ignore')
            line = line.strip()
            if line:
                print(line)
                regexTmpl = ""
                if miner == 'xmrig' and 'speed' in line: # [2025-01-14 08:33:06.380]  miner    speed 10s/60s/15m 4808.4 4744.6 n/a H/s max 4808.4 H/s
                    regexTmpl= r"speed\s+10s/60s/15m\s+([\d\.]+).*?([kmgt]?h/s)"
                #elif miner == 'srbminer-multi' and 'total' in line:
                #    regexTmpl= r"total\s*:?\s*([\d\.]+)\s+([kmgt]?h/s)"
                elif miner == 'cpuminer-opt-rplant' and 'Accepted' in line: #  Accepted 15/15 (100.0%), diff 0.00000711, 990.92 H/s, 26.424 sec (167ms)
                    regexTmpl= r"([\d\.]+)\s*([kmgt]?h/s)"
                else:
                    continue
                
                match = re.search(regexTmpl, line, re.IGNORECASE)
                if match:
                    _g_hashrate = [match.group(1), match.group(2)]
                    print(f"{YELLOW}STAN LOG LINE: hashrate - {_g_hashrate[0]} {_g_hashrate[1]}{RESET}")
            
    except UnicodeDecodeError as e:
        logger.error(f"Unicode decode error: {e}")
    except Exception as e:
        logger.error(f"Error reading process output: {e}")

def signal_handler(sig, frame):
    logger.info('Termination signal received. Stopping client...')
    _g_shutdown_event.set()
    terminate_process()
    sys.exit(0)

def terminate_process():
    global _g_process, _g_hashrate
    if _g_process:
        logger.debug(f"Terminating process PID {_g_process.pid}...")
        _g_hashrate = [0, '']
        try:
            subprocess.run(f"TASKKILL /F /PID {_g_process.pid} /T", shell=True)
            _g_process.wait(timeout=5)
            logger.debug(f"Process PID {_g_process.pid} terminated.")
        except subprocess.TimeoutExpired:
            logger.warning(f"Process PID {_g_process.pid} did not terminate in time. Killing...")
            subprocess.run(f"TASKKILL /F /PID {_g_process.pid} /T", shell=True)
            _g_process.wait()
            logger.debug(f"Process PID {_g_process.pid} killed.")
        except ProcessLookupError:
            logger.warning(f"Process PID {_g_process.pid} already terminated.")
        except Exception as e:
            logger.error(f"Error terminating process PID {_g_process.pid}: {e}")
        finally:
            _g_process = None

def send_parameters_and_get_command(server, wallet, worker, threads, command_hash):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect(server)
            client_socket.settimeout(10)

            fileobj = client_socket.makefile('rw')
            temps = []
            if (_g_config.getboolean('MAIN', 'detect_temperature')):
                temps = get_cpu_temperature()
            temps = temps if temps else [{'cpu': 0}]
            #logger.debug(f"STAN INFO: {worker} temperatures: {temps}") 

            # Prepare request
            request = {
                'wallet': wallet,
                'worker': worker,
                'threads': threads,
                'command_hash': command_hash,
                'temps': temps,
                'hashrate_value': _g_hashrate[0],
                'hashrate_unit': _g_hashrate[1],
                'client': 'Windows ' + _g_version
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
        logger.error(f"Error communicating with server {server}: {e}")
        return None      

def load_miner(name):
    try:
        miner = _g_miners[name]
        dir = os.path.join("./", name)
        dirVersion = os.path.join(dir, miner['version'])
        fileName = os.path.basename(miner['url'])
        if not os.path.exists(dirVersion):
            if os.path.exists(dir): # delete old
                shutil.rmtree(dir)
            if not os.path.exists(fileName): #download
                logger.info("Download miner " + name + " " + miner['version'])
                powershell(f"Invoke-RestMethod -Uri '{miner['url']}' -OutFile '{fileName}'")
            with zipfile.ZipFile(fileName,"r") as zip_ref:
                zip_ref.extractall(dirVersion)
            os.remove(fileName)
    except Exception as e:
        logger.error(f"Miner loading error: {e}")
        sys.exit(1)

def configIni():
    global _g_config, _g_miners
    try:
        _g_config = configparser.ConfigParser()
        _g_config.read('config.ini')
        _g_miners['binaryexpr']             = _g_config['binaryexpr']
        _g_miners['cpuminer-opt-rplant']    = _g_config['cpuminer-opt-rplant']
        _g_miners['hellminer']              = _g_config['hellminer']
        _g_miners['tnn-miner']              = _g_config['tnn-miner']
        _g_miners['srbminer-multi']         = _g_config['srbminer-multi']
        _g_miners['xmrig']                  = _g_config['xmrig']
    except Exception as e:
        logger.error(f"Error config.ini: {e}")
        sys.exit(1)

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
            logger.info("STANMINE is active")
            while not _g_shutdown_event.is_set():
                try:
                    if prev_command_hash != command_hash:
                        prev_command_hash = command_hash if command_hash else "NONE"
                        terminate_process()
                        search = re.search(r'^.*/tmp/STAN_MINER/CURRENT_MINER/\S*?(SRBMiner-Multi|xmrig|tnn-miner|hellminer) (.*)$', command, flags=re.I | re.S)

                        if search:
                            miner = search[1].lower()
                            args = search[2]
                        elif "/tmp/STAN_MINER/CURRENT_MINER/cpuminer-sse2" in command:
                            miner = "cpuminer-opt-rplant"
                            args = re.sub(r'^.*/cpuminer-sse2 (.*?)$', r'\1', command, flags=re.S)
                        elif "/tmp/STAN_MINER/CURRENT_MINER/spectre" in command:
                            miner = "binaryexpr"
                            args = re.sub(r'^.*/spectre-miner (.*?)$', r'\1', command, flags=re.S)
                        elif "/tmp/STAN_MINER/CURRENT_MINER/" in command: # most likely some unknown miner
                            logger.error("Most likely some unknown miner for the client. Mining stopped")
                            logger.error("Server command:\n------\n" + command + "\n")
                            break
                        else:
                            logger.error("When parsing commands from the server, the miner was not found\n")
                            logger.error("Server command:\n------\n" + command + "\n")
                            break

                        if (not _g_config.getboolean('MAIN', 'download_all_miners')):
                            load_miner(miner)
                        start_mining(miner, args)

                    command = send_parameters_and_get_command(server, user_wallet, worker, user_threads, prev_command_hash)
                    logger.debug(f"Waiting 120 seconds before the next poll.")
                    for _ in range(120):
                        if _g_shutdown_event.is_set():
                            break
                        time.sleep(1)

                    if command is not None:
                        command_hash = hashlib.sha256(command.encode('utf-8')).hexdigest()
                except Exception as e:
                    logger.error(f"Error sending system parameters: {e}")
                    break
        else:
            logger.info(f"Command not received. Retrying in 20 seconds...")
            time.sleep(20)
                

if __name__ == "__main__":
    version = _g_version + (" " * (15 - len(_g_version)))
    logger.info(
f'''//////////////////////////////////////////////////////////////
//                                                          //
//   #####                                                  //
//  #     # #####   ##   #    #    #     # # #    # ######  //
//  #         #    #  #  ##   #    ##   ## # ##   # #       //
//   #####    #   #    # # #  #    # # # # # # #  # #       //
//        #   #   ###### #  # #    #  #  # # #  # # ####    //
//  #     #   #   #    # #   ##    #     # # #   ## #       //
//   #####    #   #    # #    #    #     # # #    # ######  //
//                                                          //
//  Version {   version   }                                 //
//////////////////////////////////////////////////////////////''')
    configIni()
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--user_wallet", type=str, help="User wallet for mining", required=True)
    parser.add_argument("-t", "--user_threads", type=int, help="CPU threads for mining", required=False, default=0)
    parser.add_argument("-s", "--server", type=str, help="Server for mining", required=False, default=_g_config['MAIN']['server'])
    parser.add_argument("-p", "--port", type=int, help="Server port for mining", required=False, default=_g_config.getint('MAIN', 'port'))
    parser.add_argument("-w", "--worker", type=str, help="Worker name", required=True)
    parser.add_argument("--debug", help="Debug mode", required=False, action="store_true")
    args = parser.parse_args()

    if (args.debug):
        logger.info('Debug mode: enable')
        logger.setLevel(logging.DEBUG)

    # Handle termination signals
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


    if (_g_config.getboolean('MAIN', 'download_all_miners')):
        for miner in _g_miners.keys():
            load_miner(miner)
    main_loop((args.server, args.port), args.user_wallet, args.worker, args.user_threads)
    logger.info("Client stopped.")