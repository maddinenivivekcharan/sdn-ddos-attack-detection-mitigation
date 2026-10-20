# Verification record

Date: 2026-10-20. Development host: Windows, PowerShell.
Interpreter: existing workspace CPython 3.13.7 embeddable runtime.

## Executed successfully

- `python run_tests.py`: **25 tests passed**, 0 failures, 0 errors.
  These are 11 detection tests, 9 configuration tests, 5 mitigation adapter tests.
- `python -m compileall -q controller topology tests run_tests.py`: passed.
- Portable controller config, detection and mitigation imports: passed.
- Default JSON parsing and timestamped logging configuration initialization: passed.
- Git Bash `bash -n` on all four shell scripts: passed.
- README shell script references checked against actual files: passed.
- Final source directory inspected; runtime caches and logs ignored by Git.
- Secret-pattern scan found no matching private keys, GitHub tokens, AWS access
  keys or quoted password/API token assignments. This is a limited pattern scan,
  not a guarantee that arbitrary secrets could never be present.
- Git initialized only in this new project. No remote, staged changes, commits
  or pushes were created. Existing helpdesk project was left untouched.

## Not executed / unverified

WSL listing failed on this machine. No Linux Mininet, OVS or Ryu environment was
available for this run. No privileged installation or network changes were made.
The following require manual verification in the dedicated Linux VM:

1. Installing the legacy CPython 3.8 Ryu dependencies and importing Ryu/Eventlet.
2. Controller launch and loopback OpenFlow 1.3 switch connection.
3. Live host connectivity and counter polling.
4. Low-rate traffic triggering the actual switch drop rule.
5. Unaffected-client connectivity during mitigation.
6. Automatic hard-timeout expiry and FlowRemoved handling.
7. Explicit cookie deletion, recovery and topology teardown.

Run `sudo bash scripts/run_demo.sh` manually after starting the controller as
explained in README. The demo contains real assertions for items 3-7, checks
switch state, and exits with an error if a check fails. Inspect timestamped
controller observations to confirm counter monitoring. Unit mocks and compilation
do not establish compatibility or runtime success of the live stack. All example
live output in README is illustrative.
