"""OS-level process enumeration for the NFR-1 measurement harness.

Windows-native by construction. The primary backend is psutil, which is a declared
dependency of this repository (requirements.txt line 37, pyproject.toml) and enumerates
processes through the Win32 API in-process, spawning nothing. The fallback backend
shells out to PowerShell's Get-CimInstance Win32_Process, which is present on every
supported Windows host. No POSIX-only mechanism (the `ps` command, /proc) appears on any
code path, so nothing here is Linux-only.

Two soundness properties are recorded rather than assumed:

Short-lived processes. The acceptance criterion specifies a count taken immediately
before and after ten tool calls. A pure two-endpoint diff cannot observe a process that
starts and exits between the endpoints, and the retained Stop hook's `git rev-parse`
calls complete in tens of milliseconds. A harness that reported only the endpoint diff
would report zero for a component that in fact spawned repeatedly, which is the failure
mode where a check becomes indistinguishable from a no-op. ContinuousSampler therefore
polls across the window and unions everything it sees; both figures are reported, the
endpoint one because the criterion asks for it and the sampled one because it is sound.
Sampling narrows the blind spot to roughly one interval, it does not close it, and the
interval is recorded in every snapshot set so a reader can judge the residual.

Backend perturbation. The PowerShell fallback spawns a process on every snapshot,
perturbing exactly what it measures. Snapshots record which backend produced them and
whether that backend is perturbing, and the harness attributes its own spawns to a
dedicated self component rather than letting them contaminate another component's count.
"""

import json
import os
import subprocess
import sys
import threading
import time

BACKEND_PSUTIL = "psutil"
BACKEND_POWERSHELL_CIM = "powershell-cim"

PERTURBING_BACKENDS = frozenset({BACKEND_POWERSHELL_CIM})

_CIM_QUERY = (
    "Get-CimInstance Win32_Process | "
    "Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CommandLine,CreationDate | "
    "ConvertTo-Json -Compress -Depth 3"
)


class ProbeError(RuntimeError):
    """Raised when no process-enumeration backend can produce a snapshot."""


class ProcessRecord(object):
    """One observed operating-system process.

    Identity is the pair (pid, create_token), never the pid alone. Windows reuses
    process identifiers aggressively, so a pid-only key would silently equate a
    long-dead process with a newly spawned one and hide a real spawn.

    Attributes:
        pid: Operating-system process identifier.
        ppid: Parent process identifier, or None when the backend withheld it.
        name: Executable image name as reported by the backend.
        exe: Full executable path, or None when unavailable.
        cmdline: Full command line as a single string, or None when unavailable.
        create_token: Backend-supplied creation-time string, used only for identity.
        access_denied: True when the operating system refused command-line or path
            details. Such a process cannot be attributed and must be reported, never
            dropped, because an unreadable process cannot be shown to not be the
            plugin's.
    """

    __slots__ = ("pid", "ppid", "name", "exe", "cmdline", "create_token", "access_denied")

    def __init__(self, pid, ppid, name, exe, cmdline, create_token, access_denied=False):
        self.pid = int(pid)
        self.ppid = int(ppid) if ppid is not None else None
        self.name = name or ""
        self.exe = exe or None
        self.cmdline = cmdline or None
        self.create_token = str(create_token)
        self.access_denied = bool(access_denied)

    @property
    def key(self):
        """Return the reuse-safe identity tuple for this process."""
        return (self.pid, self.create_token)

    def search_text(self):
        """Return the lowercased text that component matchers are tested against."""
        parts = [self.name or "", self.exe or "", self.cmdline or ""]
        return " ".join(parts).lower()

    def to_dict(self):
        """Return a JSON-serialisable view of this record."""
        return {
            "pid": self.pid,
            "ppid": self.ppid,
            "name": self.name,
            "exe": self.exe,
            "cmdline": self.cmdline,
            "create_token": self.create_token,
            "access_denied": self.access_denied,
        }

    def __repr__(self):
        return "ProcessRecord(pid=%d, name=%r)" % (self.pid, self.name)


class Snapshot(object):
    """A point-in-time map of every process the backend could enumerate.

    Attributes:
        records: Mapping of identity key to ProcessRecord.
        captured_at: Wall-clock epoch seconds at capture.
        backend: Which enumeration backend produced this snapshot.
        errors: Per-process enumeration failures, each a short string. A non-empty
            list means the snapshot is incomplete and any verdict derived from it is
            at best indeterminate.
    """

    __slots__ = ("records", "captured_at", "backend", "errors")

    def __init__(self, records, captured_at, backend, errors=None):
        self.records = records
        self.captured_at = captured_at
        self.backend = backend
        self.errors = list(errors or [])

    @property
    def is_perturbing(self):
        """Return True when producing this snapshot itself spawned processes."""
        return self.backend in PERTURBING_BACKENDS

    def to_dict(self):
        """Return a JSON-serialisable summary, excluding the full record map."""
        return {
            "captured_at": self.captured_at,
            "backend": self.backend,
            "is_perturbing": self.is_perturbing,
            "process_count": len(self.records),
            "enumeration_errors": len(self.errors),
            "enumeration_error_samples": self.errors[:5],
        }


def psutil_available():
    """Return True when the psutil backend can be imported."""
    try:
        import psutil  # noqa: F401
    except ImportError:
        return False
    return True


def _snapshot_psutil():
    """Enumerate processes through psutil without spawning anything.

    Returns:
        Snapshot built from the Win32 API via psutil.

    Raises:
        ProbeError: If psutil cannot be imported.
    """
    try:
        import psutil
    except ImportError as exc:
        raise ProbeError("psutil backend unavailable: %s" % exc)

    records = {}
    errors = []
    for proc in psutil.process_iter(["pid", "ppid", "name", "exe", "cmdline", "create_time"]):
        info = proc.info
        pid = info.get("pid")
        if pid is None:
            continue
        denied = False
        cmdline = info.get("cmdline")
        exe = info.get("exe")
        if cmdline is None or exe is None:
            denied = True
        create_time = info.get("create_time")
        if create_time is None:
            errors.append("pid %s: no create_time; excluded to keep identity reuse-safe" % pid)
            continue
        try:
            joined = " ".join(cmdline) if cmdline else None
        except TypeError:
            joined = None
            denied = True
        record = ProcessRecord(
            pid=pid,
            ppid=info.get("ppid"),
            name=info.get("name"),
            exe=exe,
            cmdline=joined,
            create_token="%.6f" % float(create_time),
            access_denied=denied,
        )
        records[record.key] = record
    return Snapshot(records, time.time(), BACKEND_PSUTIL, errors)


def _snapshot_powershell_cim():
    """Enumerate processes through PowerShell Get-CimInstance Win32_Process.

    This backend is Windows-only and perturbing: each call spawns powershell.exe and
    usually conhost.exe. It exists so the harness still functions on a host where
    psutil is missing, not as a preferred path.

    Returns:
        Snapshot built from Win32_Process.

    Raises:
        ProbeError: If the platform is not Windows, or PowerShell fails or emits
            output that cannot be parsed.
    """
    if not sys.platform.startswith("win"):
        raise ProbeError("powershell-cim backend requires Windows; platform is %r" % sys.platform)

    command = ["powershell", "-NoProfile", "-NonInteractive", "-Command", _CIM_QUERY]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ProbeError("powershell-cim backend failed to run: %s" % exc)

    if completed.returncode != 0:
        raise ProbeError(
            "powershell-cim backend exited %d: %s" % (completed.returncode, (completed.stderr or "").strip()[:300])
        )

    try:
        payload = json.loads(completed.stdout or "[]")
    except ValueError as exc:
        raise ProbeError("powershell-cim backend emitted unparsable JSON: %s" % exc)

    if isinstance(payload, dict):
        payload = [payload]

    records = {}
    errors = []
    for entry in payload:
        pid = entry.get("ProcessId")
        if pid is None:
            continue
        created = entry.get("CreationDate")
        if created is None:
            errors.append("pid %s: no CreationDate; excluded to keep identity reuse-safe" % pid)
            continue
        cmdline = entry.get("CommandLine")
        exe = entry.get("ExecutablePath")
        record = ProcessRecord(
            pid=pid,
            ppid=entry.get("ParentProcessId"),
            name=entry.get("Name"),
            exe=exe,
            cmdline=cmdline,
            create_token=str(created),
            access_denied=(cmdline is None or exe is None),
        )
        records[record.key] = record
    return Snapshot(records, time.time(), BACKEND_POWERSHELL_CIM, errors)


def take_snapshot(preferred_backend=None):
    """Capture one process snapshot using the best available backend.

    Args:
        preferred_backend: Force a specific backend name, or None to auto-select
            psutil first and fall back to PowerShell CIM.

    Returns:
        Snapshot of every enumerable process.

    Raises:
        ProbeError: If the requested backend, or every available backend, failed.
    """
    if preferred_backend == BACKEND_PSUTIL:
        return _snapshot_psutil()
    if preferred_backend == BACKEND_POWERSHELL_CIM:
        return _snapshot_powershell_cim()
    if preferred_backend is not None:
        raise ProbeError("unknown backend %r" % preferred_backend)

    failures = []
    for factory in (_snapshot_psutil, _snapshot_powershell_cim):
        try:
            return factory()
        except ProbeError as exc:
            failures.append(str(exc))
    raise ProbeError("no process-enumeration backend succeeded: %s" % "; ".join(failures))


def endpoint_delta(before, after):
    """Return processes present in the later snapshot and absent from the earlier one.

    This is the literal reading of the acceptance criterion, a count taken immediately
    before and after the tool calls. It systematically under-reports, because any
    process that starts and exits inside the window is invisible to it. Use it for
    criterion conformance and read it alongside a sampled delta.

    Args:
        before: Snapshot captured before the measurement window.
        after: Snapshot captured after the measurement window.

    Returns:
        List of ProcessRecord, ordered by pid.
    """
    new_keys = set(after.records) - set(before.records)
    return sorted((after.records[k] for k in new_keys), key=lambda r: r.pid)


class ContinuousSampler(object):
    """Polls the process list across a measurement window and unions what it sees.

    A two-endpoint diff cannot see a process whose whole lifetime falls between the
    endpoints. This sampler reduces that blind spot to approximately one polling
    interval. It does not eliminate it: a process shorter than the interval can still
    slip through entirely, which is why observed_blind_spot_seconds is reported rather
    than the harness claiming completeness.

    Attributes:
        interval_seconds: Requested delay between polls.
        backend: Backend name forwarded to take_snapshot.
    """

    def __init__(self, interval_seconds=0.05, backend=None):
        self.interval_seconds = float(interval_seconds)
        self.backend = backend
        self._seen = {}
        self._errors = []
        self._poll_count = 0
        self._thread = None
        self._stop = threading.Event()
        self._lock = threading.Lock()

    def _run(self):
        """Poll until stopped, merging every observed process into the seen map."""
        while not self._stop.is_set():
            try:
                snap = take_snapshot(self.backend)
            except ProbeError as exc:
                with self._lock:
                    self._errors.append(str(exc))
                break
            with self._lock:
                self._seen.update(snap.records)
                self._poll_count += 1
            self._stop.wait(self.interval_seconds)

    def start(self):
        """Begin polling in a background daemon thread."""
        if self._thread is not None:
            raise RuntimeError("sampler already started")
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="nfr1-sampler", daemon=True)
        self._thread.start()

    def stop(self):
        """Stop polling and join the background thread."""
        if self._thread is None:
            return
        self._stop.set()
        self._thread.join(timeout=10)
        self._thread = None

    @property
    def poll_count(self):
        """Return how many complete polls the sampler managed."""
        with self._lock:
            return self._poll_count

    @property
    def errors(self):
        """Return polling failures recorded so far."""
        with self._lock:
            return list(self._errors)

    def seen_records(self):
        """Return every process observed during the window, keyed by identity."""
        with self._lock:
            return dict(self._seen)

    def sampled_delta(self, before):
        """Return processes seen during the window that were absent at the start.

        Args:
            before: Snapshot captured before the window opened.

        Returns:
            List of ProcessRecord, ordered by pid.
        """
        seen = self.seen_records()
        new_keys = set(seen) - set(before.records)
        return sorted((seen[k] for k in new_keys), key=lambda r: r.pid)

    def to_dict(self):
        """Return a JSON-serialisable summary of sampler coverage."""
        return {
            "interval_seconds": self.interval_seconds,
            "poll_count": self.poll_count,
            "observed_blind_spot_seconds": self.interval_seconds,
            "blind_spot_note": (
                "a process whose entire lifetime is shorter than the polling interval "
                "can still be missed; sampling narrows this window, it does not close it"
            ),
            "errors": self.errors,
        }


def current_process_lineage():
    """Return the pid chain from this process up to the root, nearest ancestor first.

    The harness uses this to attribute its own spawns and its own interpreter to a
    dedicated self component, so that measurement scaffolding never contaminates the
    count of a component under test.

    Returns:
        List of integer pids beginning with this process.
    """
    chain = [os.getpid()]
    try:
        import psutil
    except ImportError:
        return chain
    try:
        proc = psutil.Process(chain[0])
        for parent in proc.parents():
            chain.append(parent.pid)
    except psutil.Error:
        return chain
    return chain
