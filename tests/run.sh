#!/usr/bin/env bash

diff <(python3 conda-deps.py tests/experiment.py) <(cat tests/experiment.env)
diff <(python3 conda-deps.py tests/IndexedFasta.py) <(cat tests/IndexedFasta.env)
diff <(python3 conda-deps.py tests/pipeline_rnaseqqc.py) <(cat tests/pipeline_rnaseqqc.env)
