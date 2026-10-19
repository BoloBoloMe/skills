"""走产品自带的黑盒同步入口. 只转发它自己的输出."""

import subprocess
import sys

if __name__ == "__main__":
    result = subprocess.run([sys.executable, "src/service.py"], capture_output=True, text=True, check=True)
    print(result.stdout.strip())
