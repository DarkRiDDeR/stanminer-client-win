chcp 65001
while(1)
{
    python stanminer_client_win.py -u stan63 -w myWorker
    Start-Sleep -Seconds 60
}