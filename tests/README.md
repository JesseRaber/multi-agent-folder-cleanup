# Test environment

Use an isolated virtual environment. The complete suite requires Python 3.11 or newer and the dependencies pinned in `requirements-dev.txt`.

Windows PowerShell 5.1:

```powershell
py -3.14 -m venv .test-venv
.\.test-venv\Scripts\python.exe -m pip install --disable-pip-version-check -r requirements-dev.txt
.\.test-venv\Scripts\python.exe tests\run_tests.py --powershell powershell.exe
```

PowerShell 7:

```powershell
.\.test-venv\Scripts\python.exe tests\run_tests.py --powershell pwsh
```

The runner checks PyYAML before discovery and prints `blocked: PyYAML missing` with the installation command if the environment is incomplete. `--powershell` selects the engine used by Python/PowerShell parity tests; the remaining tests are unchanged.
