#!/usr/bin/env python3
"""Run a command, save complete output, return a bounded diagnostic summary."""
import argparse
import datetime
import os
from pathlib import Path
import re
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lines', type=int, default=45, help='maximum output lines (10-200)')
    parser.add_argument('--timeout', type=int, default=900, help='timeout seconds')
    parser.add_argument('--log-dir', default='.quant-logs', help='full-output log directory')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    cmd = args.command
    if cmd and cmd[0] == '--':
        cmd = cmd[1:]
    if not cmd:
        parser.error('provide command after --')
    limit = min(200, max(10, args.lines))
    folder = Path(args.log_dir).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    log = folder / f'command-{stamp}-{os.getpid()}.log'
    started = time.monotonic()
    code = 1
    try:
        with log.open('wb') as out:
            proc = subprocess.Popen(cmd, stdout=out, stderr=subprocess.STDOUT, start_new_session=True)
            try:
                code = proc.wait(timeout=max(1, args.timeout))
            except subprocess.TimeoutExpired:
                import signal
                os.killpg(proc.pid, signal.SIGKILL)
                proc.wait()
                code = 124
    except OSError as exc:
        log.write_text(f'Command failed to start: {exc}\n')
        code = 127
    duration = time.monotonic() - started
    # Stream full log once; retain only the tail and pytest summary/failure IDs.
    from collections import deque
    tail = deque(maxlen=limit)
    failures = []
    summary = []
    total_lines = 0
    with log.open('r', errors='replace') as stream:
        for line in stream:
            total_lines += 1
            clean = line.rstrip('\n')
            tail.append(clean[:400])
            if re.match(r'^(FAILED|ERROR)\s+\S+', clean):
                if len(failures) < 25:
                    failures.append(clean[:300])
            if re.search(r'\b(?:passed|failed|errors?|skipped|xfailed|xpassed)\b', clean) and (' in ' in clean or clean.startswith('=') or clean.startswith('no tests ran')):
                if len(summary) < 10:
                    summary.append(clean[:300])
    print(f'EXIT_CODE: {code} | DURATION_SECONDS: {duration:.1f} | OUTPUT_LINES: {total_lines}')
    print(f'FULL_LOG: {log}')
    if summary:
        print('PYTEST_SUMMARY:')
        for item in summary[-3:]:
            print(item)
    if failures:
        print('FAILED_TESTS:')
        for item in failures:
            print(item)
    print(f'LAST_{limit}_LINES:')
    for item in tail:
        print(item)
    return code


if __name__ == '__main__':
    sys.exit(main())
