::pushd %~dp0
chcp 65001
cd %~dp0
:start
python stanminer_client_win.py -u UQCFVXtlCUjTY5n1zdwXbALgsbYQK1WrZUfAzU3shSyMx5D8
pause
goto start