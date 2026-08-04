"""Run a subprocess under a progress lease instead of a wall-clock timeout.

This is the replacement for ``subprocess.run(..., timeout=N)`` on the long-running
pipeline path. The difference is not the presence or absence of a bound; it is
what the bound measures.

``subprocess.run(timeout=N)`` kills a child that has been alive for N seconds. On
the Step 1 planning path the child is the ``claude`` CLI, whose latency is not
bounded by anything this repository controls, so N was always a guess about
someone else's machine. The composite 75-second figure at
``task_orchestration.py:160`` was a guess about a guess.

``run_supervised`` never reads total elapsed time. It reads the gap since the
last byte of output. A child that keeps writing renews its lease and runs as long
as it needs to; a child that has written nothing for a full renewal interval is
not slow, it has stopped, and terminating it is a no-progress decision rather
than a deadline. With no interval configured -- the default -- nothing is
terminated at all, which is what NFR-2's "default to unbounded" requires.

WHAT THIS COSTS, STATED PLAINLY
-------------------------------
Progress is inferred from output, so a child that genuinely works in silence for
longer than the configured interval is indistinguishable from a hung one. That is
why the interval defaults to None. It is also why the streaming caller, whose
stderr is inherited rather than piped so the user sees live progress, renews on
stdout alone: its evidence channel is narrower, and a narrower channel is a
reason to leave its lease unbounded, not a reason to pretend the evidence is
there.
"""

import subprocess
import threading
import time

from .breaker import get_breaker
from .lease import Lease, LeaseExpired

POLL_INTERVAL_SECONDS = 0.05

TERMINATE_POLLS = 100


class SupervisedResult:
    """Outcome of a supervised subprocess run.

    Attributes:
        returncode: Child exit status.
        stdout: Captured standard output, or an empty string when not piped.
        stderr: Captured standard error, or an empty string when inherited.
        renewals: How many progress events renewed the lease.
        duration: Wall-clock seconds the child ran, recorded for the breaker's
            slow-call rate and for nothing else.
    """

    def __init__(self, returncode, stdout, stderr, renewals, duration):
        """Store the run outcome.

        Args:
            returncode: Child exit status.
            stdout: Captured standard output.
            stderr: Captured standard error.
            renewals: Count of lease renewals.
            duration: Seconds the child ran.
        """
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.renewals = renewals
        self.duration = duration


class NoProgress(RuntimeError):
    """Raised when a supervised child produced no output for a full lease interval.

    Distinct from a timeout by construction: it reports silence, not duration, and
    a child that ran for hours while streaming never raises it.
    """


def _drain(stream, sink, lease):
    """Copy a child stream into a sink, renewing the lease on every chunk.

    The read is ``read1``, not ``read``. ``read(n)`` blocks until it has n bytes
    or reaches EOF, so a child emitting a byte at a time would produce no
    renewal until its buffer happened to fill -- and the lease would lapse on a
    child that was demonstrably working. ``read1`` performs at most one raw read
    and returns whatever is available, which is exactly the progress evidence
    this mechanism is built on. The first version of this function used
    ``read(1024)`` and killed a healthy child in its own test.

    Args:
        stream: Readable binary stream from the child.
        sink: List collecting the chunks read.
        lease: Lease renewed on each chunk as evidence of progress.
    """
    try:
        while True:
            chunk = stream.read1(65536)
            if not chunk:
                break
            sink.append(chunk)
            lease.renew()
    except (ValueError, OSError):
        return
    finally:
        try:
            stream.close()
        except (ValueError, OSError):
            pass


def _feed(stream, payload):
    """Write the child's stdin payload and close the pipe.

    Runs on its own thread because a payload larger than the pipe buffer would
    otherwise deadlock against a child that is waiting to be read.

    Args:
        stream: Writable binary stream to the child.
        payload: Bytes to send, or None to close immediately.
    """
    try:
        if payload:
            stream.write(payload)
            stream.flush()
    except (ValueError, OSError):
        pass
    finally:
        try:
            stream.close()
        except (ValueError, OSError):
            pass


def run_supervised(
    cmd,
    input=None,
    capture_stderr=True,
    lease_interval=None,
    lease_name="subprocess",
    env=None,
    cwd=None,
    encoding="utf-8",
    errors="replace",
    breaker_name=None,
):
    """Run a child process bounded by progress rather than by elapsed time.

    Args:
        cmd: Command list passed to Popen.
        input: Text written to the child's stdin, or None.
        capture_stderr: Pipe and capture stderr when True; inherit the parent's
            stderr when False, so a long-running child's progress stays visible.
        lease_interval: Seconds of silence tolerated before the child is
            terminated. None, the default, means the child is never terminated
            for silence.
        lease_name: Label for the lease, used in errors and logs.
        env: Environment mapping for the child.
        cwd: Working directory for the child.
        encoding: Text encoding for the child's streams.
        errors: Decoding error policy for the child's streams.
        breaker_name: External dependency whose circuit breaker should observe
            this call, or None to record nothing.

    Returns:
        SupervisedResult: The child's exit status and captured output.

    Raises:
        NoProgress: When the lease lapsed and the child was terminated.
        OSError: When the child could not be started.
    """
    lease = Lease(lease_name, interval=lease_interval)
    breaker = get_breaker(breaker_name) if breaker_name else None
    started = time.monotonic()

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE if input is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE if capture_stderr else None,
        env=env,
        cwd=cwd,
    )
    payload = input.encode(encoding, errors) if input is not None else None

    out_chunks = []
    err_chunks = []
    workers = []

    if proc.stdin is not None:
        workers.append(threading.Thread(target=_feed, args=(proc.stdin, payload), daemon=True))
    if proc.stdout is not None:
        workers.append(threading.Thread(target=_drain, args=(proc.stdout, out_chunks, lease), daemon=True))
    if proc.stderr is not None:
        workers.append(threading.Thread(target=_drain, args=(proc.stderr, err_chunks, lease), daemon=True))
    for worker in workers:
        worker.start()

    lapse = None
    while True:
        if proc.poll() is not None:
            break
        try:
            lease.check()
        except LeaseExpired as exc:
            lapse = exc
            _terminate(proc)
            break
        time.sleep(POLL_INTERVAL_SECONDS)

    returncode = proc.wait()
    for worker in workers:
        worker.join()
    duration = time.monotonic() - started

    if lapse is not None:
        if breaker is not None:
            breaker.record_failure(duration)
        raise NoProgress(str(lapse))

    if breaker is not None:
        if returncode == 0:
            breaker.record_success(duration)
        else:
            breaker.record_failure(duration)

    stdout = b"".join(out_chunks).decode(encoding, errors)
    stderr = b"".join(err_chunks).decode(encoding, errors)
    return SupervisedResult(returncode, stdout, stderr, lease.renewals, duration)


def _terminate(proc, polls=TERMINATE_POLLS):
    """End a child that stopped making progress, escalating if it ignores the first ask.

    The escalation is bounded by a POLL COUNT rather than by a grace deadline,
    for the same reason the run itself is: a count is a bound on work done, and
    reintroducing a wall-clock deadline here to enforce a rule against wall-clock
    deadlines would be an odd way to keep it. The child is already doomed at this
    point, so the only question is how many times to ask politely first.

    Args:
        proc: The Popen object to end.
        polls: How many times to check for a clean exit before killing.
    """
    try:
        proc.terminate()
    except OSError:
        return
    for _ in range(polls):
        if proc.poll() is not None:
            return
        time.sleep(POLL_INTERVAL_SECONDS)
    if proc.poll() is None:
        try:
            proc.kill()
        except OSError:
            pass
