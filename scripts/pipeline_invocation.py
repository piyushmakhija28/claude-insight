"""Which caller is allowed to start the pipeline (PRD FR-5 / SRS FR-15, issue V2-028).

WHAT THIS MODULE IS FOR, AND WHAT IT DELIBERATELY IS NOT FOR
------------------------------------------------------------
V2-028 carries two acceptance criteria:

  AC 1  A user prompt no longer invokes ``scripts/3-level-flow.py``.
  AC 2  Pipeline execution begins only from an explicit SRS FR-17 command.

AC 1 is a property of a REGISTRATION -- the ``UserPromptSubmit`` entry in a live
settings file. Nothing in this repository can establish it, and the project owner
ruled that no agent may write to a live settings file for this issue. AC 1 is
therefore deferred, and this module makes no attempt at it.

AC 2 is a property of the CODE PATH, and that is reachable here. Before this
module existed, "which caller started this run" was answered only by inference:
the hook supplied the prompt on stdin and the dispatcher supplied it as
``--message=``. That is a difference in habit, not a rule -- either caller could
have used either shape, and no test could tell them apart. This module replaces
the inference with a declaration that the caller must make, and that the entry
point refuses to run without.

THE DECLARATION IS AN ARGUMENT, NOT AN ENVIRONMENT VARIABLE
-----------------------------------------------------------
``--invoked-by=<command>`` is passed on the command line, and one of the six
FR-17 command names is the only accepted value. An environment variable was
rejected for a specific reason: the engine starts ``claude`` CLI subprocesses,
and every one of them would inherit the variable. An inherited authorization is
an authorization nobody made, which is exactly the property this module exists to
remove. A command-line argument reaches one process and stops there.

THERE IS NO ESCAPE HATCH, AND THAT IS THE POINT
------------------------------------------------
No environment variable disables this gate, and no filename or working directory
exempts a caller from it. An opt-out would reintroduce the situation the gate was
built to end -- a run that begins without anybody having asked for it. A caller
that legitimately needs the pipeline outside a slash command (a container
entry point, a manual CLI run) declares which FR-17 command it stands in for.
That declaration is a deliberate act, it appears in the process arguments, and a
test can read it.

WHY THE COMMAND NAMES ARE REPEATED HERE
----------------------------------------
``plugin/scripts/pipeline_entry.py`` owns the same six names. They are not
imported from it, because an installed plugin runs from the plugin manager's
cache and cannot import the engine, nor the engine the plugin -- measured during
V2-016 and recorded in that module. The two lists are therefore a wire contract
between two trees that cannot see each other, and
``tests/test_pipeline_invocation_authorization.py`` asserts they are equal so
they cannot drift apart silently.
"""

import sys
from dataclasses import dataclass

INVOCATION_FLAG = "--invoked-by"

INVOCATION_PREFIX = INVOCATION_FLAG + "="

HELP_FLAGS = ("--help", "-h")

FR17_COMMANDS = ("plan", "implement", "review", "document", "release", "run-pipeline")

DISCARDED_MESSAGE_PREFIXES = ("/", "!")

VERDICT_AUTHORIZED = "AUTHORIZED"

VERDICT_HELP = "HELP"

VERDICT_UNDECLARED = "UNDECLARED"

VERDICT_EMPTY_DECLARATION = "EMPTY_DECLARATION"

VERDICT_UNKNOWN_COMMAND = "UNKNOWN_COMMAND"

REFUSING_VERDICTS = (VERDICT_UNDECLARED, VERDICT_EMPTY_DECLARATION, VERDICT_UNKNOWN_COMMAND)

EXIT_NOT_STARTED = 0

EXIT_BAD_DECLARATION = 2


@dataclass(frozen=True)
class Authorization:
    """The outcome of asking whether a caller may start the pipeline.

    Attributes:
        authorized: True when the run may proceed.
        verdict: One of the VERDICT_* constants, naming why.
        command: The declared FR-17 command name, or "" when none was declared.
        detail: One sentence naming what was found, for the refusal report.
    """

    authorized: bool
    verdict: str
    command: str
    detail: str


def wants_help(argv):
    """Report whether the caller asked for the entry point's help text.

    Help is answered without authorization because printing usage starts no
    pipeline step. Refusing it would hide the very text that names the flag a
    refused caller needs.

    Args:
        argv: Argument strings excluding the program name.

    Returns:
        bool: True when a help flag is present.
    """
    return any(argument in HELP_FLAGS for argument in argv)


def declared_value(argv):
    """Return the value declared with the invocation flag, or None.

    The match is on the exact ``--invoked-by=`` prefix, so neighbouring flag
    names such as ``--invoked-by-someone=plan`` and ``--not-invoked-by=plan`` do
    not satisfy it, and neither does the bare ``--invoked-by`` with a separate
    argument. A gate that accepted near-misses would be a gate that could be
    passed by accident.

    Args:
        argv: Argument strings excluding the program name.

    Returns:
        str or None: The declared value verbatim, or None when absent.
    """
    for argument in argv:
        if argument.startswith(INVOCATION_PREFIX):
            return argument[len(INVOCATION_PREFIX) :]
    return None


def saw_bare_flag(argv):
    """Report whether the flag appeared without its ``=value`` form.

    Args:
        argv: Argument strings excluding the program name.

    Returns:
        bool: True when the flag name appeared on its own.
    """
    return INVOCATION_FLAG in argv


def authorize(argv):
    """Decide whether this invocation may start the pipeline.

    Args:
        argv: Argument strings excluding the program name.

    Returns:
        Authorization: The verdict, and enough detail to report it.
    """
    if wants_help(argv):
        return Authorization(True, VERDICT_HELP, "", "help was requested; no pipeline step runs")

    raw = declared_value(argv)
    if raw is None:
        if saw_bare_flag(argv):
            return Authorization(
                False,
                VERDICT_UNDECLARED,
                "",
                "{0} was given without a value; the form is {1}<command>".format(INVOCATION_FLAG, INVOCATION_PREFIX),
            )
        return Authorization(
            False,
            VERDICT_UNDECLARED,
            "",
            "no {0} declaration was present in the arguments".format(INVOCATION_PREFIX),
        )
    if raw == "":
        return Authorization(
            False,
            VERDICT_EMPTY_DECLARATION,
            "",
            "{0} declared an empty command name".format(INVOCATION_PREFIX),
        )
    if raw not in FR17_COMMANDS:
        return Authorization(
            False,
            VERDICT_UNKNOWN_COMMAND,
            raw,
            "{0!r} is not one of the six SRS FR-17 commands".format(raw),
        )
    return Authorization(True, VERDICT_AUTHORIZED, raw, "declared by the SRS FR-17 command {0!r}".format(raw))


def refusal_lines(authorization):
    """Render the refusal a caller sees, naming the cause and the remedy.

    A refusal that only said "not allowed" would be indistinguishable from a
    broken engine. Every line here names something the caller can act on: what
    was found, what the rule is, and which six names satisfy it.

    Args:
        authorization: A refusing Authorization.

    Returns:
        list: Lines to print, without trailing newlines.
    """
    return [
        "[REFUSED] pipeline execution did not start: {0}.".format(authorization.detail),
        "[REFUSED] SRS FR-15 requires that a run begin only from an explicit SRS FR-17 command.",
        "[REFUSED] Declare one with {0}<command>, where <command> is one of: {1}.".format(
            INVOCATION_PREFIX, ", ".join(FR17_COMMANDS)
        ),
        "[REFUSED] The supported route is the plugin dispatcher, which declares this for you.",
    ]


def refusal_exit_code(authorization):
    """Return the process status a refusal should exit with.

    The two refusals are not the same kind of event and must not report the same
    way. An UNDECLARED run is what a hook registration produces: nobody asked for
    the pipeline, nothing is wrong, and failing there would turn a correct
    refusal into a broken hook. A declaration that was ATTEMPTED and got the name
    wrong is a caller error, and reporting success for it would hide a typo that
    silently costs the caller a whole run.

    Args:
        authorization: A refusing Authorization.

    Returns:
        int: EXIT_NOT_STARTED for an absent declaration, EXIT_BAD_DECLARATION
        for one that was attempted and rejected.
    """
    if authorization.verdict == VERDICT_UNDECLARED:
        return EXIT_NOT_STARTED
    return EXIT_BAD_DECLARATION


def enforce_explicit_invocation(argv, stream=None):
    """Stop the process unless an explicit SRS FR-17 command declared this run.

    This is called before the entry point imports the engine or reads its
    configuration, so a run nobody asked for costs the import of this module and
    nothing else. It is the earliest point at which the question can be answered.

    Args:
        argv: Argument strings excluding the program name.
        stream: Where the refusal is written. Defaults to standard error, so it
            never contaminates a hook's standard output.

    Returns:
        Authorization: The permitting verdict, when the run may proceed.

    Raises:
        SystemExit: When the run is refused.
    """
    authorization = authorize(argv)
    if authorization.authorized:
        return authorization
    target = sys.stderr if stream is None else stream
    for line in refusal_lines(authorization):
        print(line, file=target)
    raise SystemExit(refusal_exit_code(authorization))


def discarded_message_prefix(message):
    """Return the prefix that would make the entry point discard a message.

    ``scripts/3-level-flow.py`` treats a message beginning with "/" or "!" as a
    slash or shell command and returns without running any step. That behaviour
    predates this issue and remains correct for the caller it was written for,
    but it is reported rather than performed silently: a run that reaches no step
    and exits zero is otherwise indistinguishable from one that succeeded.

    Args:
        message: The task text.

    Returns:
        str or None: The offending prefix, or None when the message is usable.
    """
    if not message:
        return None
    for prefix in DISCARDED_MESSAGE_PREFIXES:
        if message.startswith(prefix):
            return prefix
    return None


def discarded_message_lines(prefix):
    """Render the report for a message the entry point will not act on.

    Args:
        prefix: The offending prefix returned by discarded_message_prefix.

    Returns:
        list: Lines to print, without trailing newlines.
    """
    return [
        "[SKIPPED] the task begins with {0!r}, which this entry point treats as a slash".format(prefix),
        "[SKIPPED] or shell command and discards without running any pipeline step.",
        "[SKIPPED] Nothing ran. Rephrase the task so it does not start with {0}.".format(
            " or ".join(repr(item) for item in DISCARDED_MESSAGE_PREFIXES)
        ),
    ]
