import os
path = "../opentuner/opentuner/utils/adddeps.py"

if os.path.isfile(path):
    target = os.path.join(os.path.dirname(__file__), path)
    execfile(target, dict(__file__=target))
