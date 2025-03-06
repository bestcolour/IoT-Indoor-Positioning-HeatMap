import os
import sys

if len(sys.argv) < 2:
    print("Usage: python pip_install.py <package>")
    sys.exit(1)

package = " ".join(sys.argv[1:])
os.system(f"pip install {package}")
os.system("pip freeze > requirements.txt")
print(f"{package} installed and requirements.txt updated!")