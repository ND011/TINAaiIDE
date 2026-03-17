import subprocess
from pathlib import Path
from datetime import datetime

# ... (previous code)

def log_execution(command, cwd, exit_code):
    log_file = Path('.kiro/log/') / f'execution_log_{datetime.now().strftime("%Y%m%d%H%M%S")}.txt'
    with open(log_file, 'w') as file:
        file.write(f"Timestamp: {datetime.now()}\n")
        file.write(f"Command: {command}\n")
        file.write(f"CWD: {cwd}\n")
        file.write(f"Exit Code: {exit_code}\n")

try:
    result = subprocess.run(command, cwd=str(file_path.parent), shell=True, check=True)
    log_execution(command, str(file_path.parent), result.returncode)
    print(f"Command executed successfully. Exit Code: {result.returncode}")
except subprocess.CalledProcessError as e:
    log_execution(command, str(file_path.parent), e.returncode)
    print(f"Execution failed with error code {e.returncode}: {e.stderr.decode()}")