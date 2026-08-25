import json
import subprocess

payload = {
    "code": "ASSETS = ['SPY']\ndef oops(:\n  pass\n",
    "start": "2018-01-01",
}
p = subprocess.run(
    ["python", "backtest/sandbox_runner.py"],
    input=json.dumps(payload),
    text=True,
    capture_output=True,
)
print("stdout:", p.stdout)
print("stderr_tail:", (p.stderr or "")[-200:])
obj = json.loads(p.stdout.strip().splitlines()[-1])
assert obj["ok"] is False
assert obj["error"]["type"] == "SyntaxError"
assert obj["error"]["line"] == 2
print("OK structured syntax error")
