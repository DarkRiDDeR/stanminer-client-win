Windows client for StanMiner (https://stanvps.ddns.net/)

# Start example

run the script as administrator `start.bat` 

or execute the command:

``python stanminer_client_win.py -u UQCFVXtlCUjTY5n1zdwXbALgsbYQK1WrZUfAzU3shSyMx5D8 -t 3``

- -u - your account
- -t - number of threads

# Config.ini

After the first run of the script, an additional file ``config.ini`` with settings will be created. In which, in particular, you can specify the name of the worker

```
[MAIN]
server = stanvps.ddns.net
port = 8084
worker = win-worker-test
hide_mining_window = false
detect_temperature = false
libre_hardware_monitor = 127.0.0.1:8085
```

**Ports:**

- 8084 - standart server
- 8184 - dev server

# Install

First, ensure that you are using an administrative PowerShell.

## Install chocolatey

Chocolatey is software management automation for Windows that wraps installers, executables, zips, and scripts into compiled packages. https://chocolatey.org/install

Install with powershell:

``Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))``


## Install python

Download and install python using the following command

``choco install -y python3``

You can check the version to verify if Python was successfully installed as follows

``python --version``

## Optionally. Install [Libre-hardware-monitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor) for monitoring CPU temperature

Install with powershell:

``choco install libre-hardware-monitor``

Run program **Libre-hardware-monitor** (fork of Open Hardware Monitor with updates) and select:

- Options - Run On Windows Startup
- Options - Remote Web Server - Run
- Options - Remote Web Server - Port = 8085
- File - Hardware - Only select CPU

You can check it in your browser using your local IP:

http://127.0.0.1:8085/


Then set config.ini flags:

```
detect_temperature = true
libre_hardware_monitor = 127.0.0.1:8085
````

# License

MIT License
