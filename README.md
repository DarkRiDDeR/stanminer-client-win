Windows client for StanMiner (https://stanvps.ddns.net/)

**Current version - 0.3.0-beta**

see CHANGELOG.md

# Start example

run the script as administrator `start.bat` 

or execute the command:

``python stanminer_client_win.py -u UQCFVXtlCUjTY5n1zdwXbALgsbYQK1WrZUfAzU3shSyMx5D8 -w myWorker -t 6``

# Command line parameters

| Name                    | Short name | Required parameter | Type      | Description                                    |
|-------------------------|------------|--------------------|-----------|------------------------------------------------|
| --user_wallet           | -u         | **Required**       | String    | Your account wallet                            |
| --user_threads          | -t         | **Required**       | Integer   | CPU threads for mining                         |
| --server                | -s         | -                  | String    | Server for mining                              |
| --port                  | -p         | -                  | Integer   | Server port for mining                         |
| --worker                | -w         | -                  | String    | Worker name                                    |
| --debug                 |            | -                  |           | Debug mode                                     |


**Ports:**

- 8101 - standart server
- 8102 - dev server

# config.ini

After the first run of the script, an additional file ``config.ini`` with settings will be created. In which, in particular, you can specify the name of the worker

```
[MAIN]
server = stanvps.ddns.net
port = 8101
worker = win-worker-test
detect_temperature = false
libre_hardware_monitor = 127.0.0.1:8085
```

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

## Problem with ANSI color on Windows Console

The program intercepts the miners output buffer and redirects it. It has not yet been possible to preserve the color highlighting of symbols for some miners. Xmrig is one of them.
The maximum that can be highlighted is the parameters output by the client, example  the hashrate "STAN LOG LINE: hashrate - 8770.5 H/s" is highlighted in yellow.

On old builds (Windows 10 1909 or prior), Windows only recognizes the ESC code, but it is possible for Windows to recognize the ESC code \033 (or other depending on the language) with a modification in the record (regedit.exe).

If even highlighting the "STAN LOG LINE: hashrate - 8770.5 H/s" color doesn't work for you, you can still try this method.

For modification, you need to run the command below (on CMD as administrator):

``reg add HKEY_CURRENT_USER\Console /v VirtualTerminalLevel /t REG_DWORD /d 0x00000001 /f``

In case of error (it'll have no error, but...), here is the command to undo: (on CMD as administrator)

``reg add HKEY_CURRENT_USER\Console /v VirtualTerminalLevel /t REG_DWORD /d 0x00000000 /f``

# License

MIT License
