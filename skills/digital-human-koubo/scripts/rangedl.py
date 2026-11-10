"""多连接分片下载：每个文件切 N 段并行，单段失败自动续传重试；全部完成后解码校验"""
import concurrent.futures as cf
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

N = 6


def response_headers(text):
    status, headers = None, {}
    for line in text.splitlines():
        if line.startswith('HTTP/'):
            status, headers = int(line.split()[1]), {}
        elif ':' in line:
            key, value = line.split(':', 1)
            headers[key.lower()] = value.strip()
    return status, headers


def size(url):
    result = subprocess.run(['curl', '-fsSI', '--http1.1', '--max-time', '30', url],
                            capture_output=True, text=True, encoding='iso-8859-1')
    status, headers = response_headers(result.stdout)
    length = headers.get('content-length', '')
    if result.returncode or status != 200 or not length.isdigit() or int(length) <= 0:
        raise RuntimeError(f'HEAD failed or has no positive Content-Length (HTTP {status}, curl {result.returncode})')
    return int(length)


def part(url, path, a, b, total):
    path = Path(path)
    needed = b - a + 1
    with tempfile.TemporaryDirectory(prefix='dh-range-') as folder:
        headers_file, body_file = Path(folder) / 'headers', Path(folder) / 'body'
        for _ in range(30):
            have = path.stat().st_size if path.exists() else 0
            if have == needed:
                return True
            if have > needed:
                raise RuntimeError('Existing part exceeds its requested range')
            start = a + have
            expected = b - start + 1
            headers_file.write_text('', encoding='ascii')
            body_file.unlink(missing_ok=True)
            result = subprocess.run([
                'curl', '-fsS', '--http1.1', '--max-time', '60', '--max-filesize', str(expected),
                '-D', str(headers_file), '-o', str(body_file), '-r', f'{start}-{b}', url,
            ], capture_output=True)
            status, headers = response_headers(headers_file.read_text(encoding='iso-8859-1'))
            if status is None and result.returncode:
                continue  # No HTTP response: retry without admitting any bytes.
            if status != 206:
                raise RuntimeError(f'Range request requires HTTP 206, received {status} (curl {result.returncode})')
            match = re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)', headers.get('content-range', ''), re.I)
            if not match or tuple(map(int, match.groups())) != (start, b, total):
                raise RuntimeError('Content-Range does not match the requested interval and object size')
            length = headers.get('content-length')
            if length is not None and (not length.isdigit() or int(length) != expected):
                raise RuntimeError('Content-Length does not match the requested interval')
            received = body_file.stat().st_size if body_file.exists() else 0
            if received > expected or (result.returncode == 0 and received != expected):
                raise RuntimeError('Response body length does not match the requested interval')
            # Only a validated, interrupted prefix may be resumed. Never accept an
            # HTTP error body or declare a nonzero curl result complete.
            if result.returncode and (result.returncode not in (18, 28, 56) or received == expected):
                raise RuntimeError(f'Range transfer failed (curl {result.returncode})')
            if received:
                with path.open('ab') as out, body_file.open('rb') as source:
                    shutil.copyfileobj(source, out)
                if have + received == needed:
                    return True
    raise RuntimeError('Range transfer exhausted 30 attempts')


def fetch(tid, url):
    n = size(url)
    step = (n + N - 1) // N
    ranges = [(a, min(n - 1, a + step - 1)) for a in range(0, n, step)]
    paths = [Path(f'.p{tid}_{i}') for i in range(len(ranges))]
    # Each invocation starts a new object; only in-flight verified parts resume.
    for i in range(N):
        Path(f'.p{tid}_{i}').unlink(missing_ok=True)
    with cf.ThreadPoolExecutor(N) as ex:
        results = list(ex.map(lambda item: part(url, item[0], *item[1], n), zip(paths, ranges)))
    if not all(results):
        raise RuntimeError('Not all ranges completed')
    with tempfile.TemporaryDirectory(prefix='.rangedl-', dir='.') as folder:
        candidate = Path(folder) / 'download'
        with candidate.open('wb') as out:
            for path, (a, b) in zip(paths, ranges):
                if path.stat().st_size != b - a + 1:
                    raise RuntimeError('Part length changed before merge')
                with path.open('rb') as source:
                    shutil.copyfileobj(source, out)
        result = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(candidate), '-f', 'null', '-'],
                                capture_output=True, text=True, encoding='utf-8', errors='replace')
        if result.returncode or result.stderr.strip():
            raise RuntimeError(f'Decode validation failed (ffmpeg {result.returncode}): {result.stderr.strip()[:160]}')
        os.replace(candidate, f'renoise-{tid}')
    for path in paths:
        path.unlink()
    return tid, n, True, 'OK'


def main():
    try:
        with open('urls.txt', encoding='utf-8') as source:
            jobs = [line.split() for line in source if line.strip()]
        if any(len(job) != 2 for job in jobs) or len({job[0] for job in jobs}) != len(jobs):
            raise ValueError('urls.txt needs one unique taskId and URL per line')
    except (OSError, ValueError) as error:
        print(f'BAD {error}', file=sys.stderr, flush=True)
        return 1
    failed = False
    with cf.ThreadPoolExecutor(4) as ex:
        pending = {ex.submit(fetch, *job): job[0] for job in jobs}
        for future in cf.as_completed(pending):
            try:
                print(*future.result(), flush=True)
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
                failed = True
                print(f'{pending[future]} BAD {error}', file=sys.stderr, flush=True)
    return int(failed)


if __name__ == '__main__':
    sys.exit(main())
