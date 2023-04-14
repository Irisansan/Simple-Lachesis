#!/bin/bash
set -eou pipefail

python3 automate_graphing.py
cd ../PyLachesis
pwd
python3 automate_lachesis.py
cd ../
git add . 
git commit -m "feat: updated graph tests"
git push -u origin