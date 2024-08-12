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
worker = win-worker-test
hide_mining_window = false
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

# License

MIT License
