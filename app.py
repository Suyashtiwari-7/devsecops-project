import os
import subprocess
import hashlib

def insecure_functions():
    # 1. Hardcoded Password (HIGH/CRITICAL Risk)
    secret_password = "super_secret_password_123!"
    
    # 2. Command Injection / Unsafe Subprocess (HIGH Risk)
    user_input = "dir"
    subprocess.call(user_input, shell=True)
    
    # 3. Weak Cryptography - MD5 (MEDIUM Risk)
    m = hashlib.md5()
    
    # 4. Use of Assert (LOW Risk)
    assert secret_password != ""
    
if __name__ == "__main__":
    insecure_functions()