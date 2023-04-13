#!/bin/bash

set -eou pipefail

python3 automate_graphing.py
git add . 
git commit -m "feat: updated graph tests"
git push -u origin