from __future__ import annotations

import logging
import subprocess
import sys

import pytest
import pytest_mock

import build._ctx as ctx


pytestmark = pytest.mark.contextvars


def test_unknown_context_attribute() -> None:
    name = 'missing'
    with pytest.raises(AttributeError, match='missing'):
        getattr(ctx, name)


def test_default_ctx_logger(caplog: pytest.LogCaptureFixture) -> None:
    ctx.log('foo')

    [record] = caplog.records
    assert record.name == 'build'
    assert record.levelno == logging.INFO
    assert record.message == 'foo'


def test_ctx_custom_logger(mocker: pytest_mock.MockerFixture) -> None:
    log_stub = mocker.stub('custom_logger')

    ctx.LOGGER.set(log_stub)
    ctx.log('foo')

    log_stub.assert_called_once_with('foo')


def test_ctx_custom_logger_with_custom_verbosity(mocker: pytest_mock.MockerFixture) -> None:
    log_stub = mocker.stub('custom_logger')

    def log(message: str, **_kwargs: object) -> None:
        if ctx.verbosity >= 9000:
            log_stub(message)

    ctx.LOGGER.set(log)
    ctx.log('foo')
    ctx.VERBOSITY.set(9000)
    ctx.log('bar')

    log_stub.assert_called_once_with('bar')


@pytest.mark.parametrize(
    ('verbosity', 'kwarg_origins'),
    [
        (0, []),
        (1, [('subprocess', 'cmd'), ('subprocess', 'stdout')]),
    ],
)
def test_custom_subprocess_runner_ctx_logging(
    mocker: pytest_mock.MockerFixture, verbosity: int, kwarg_origins: list[tuple[str, ...]]
) -> None:
    log_stub = mocker.stub('custom_logger')

    ctx.LOGGER.set(log_stub)
    ctx.VERBOSITY.set(verbosity)

    ctx.run_subprocess([sys.executable, '-m', 'build', '-V'])

    assert log_stub.call_count == len(kwarg_origins)
    assert [c.kwargs['kind'] for c in log_stub.call_args_list] == kwarg_origins


@pytest.mark.parametrize('verbosity', [0, 1])
def test_subprocess_invalid_utf8_preserves_failure(mocker: pytest_mock.MockerFixture, verbosity: int) -> None:
    log_stub = mocker.stub('custom_logger')
    ctx.LOGGER.set(log_stub)
    ctx.VERBOSITY.set(verbosity)
    command = [sys.executable, '-c', "import os; os.write(2, b'failed: \\xff\\n'); raise SystemExit(7)"]

    with pytest.raises(subprocess.CalledProcessError) as caught:
        ctx.run_subprocess(command)

    assert caught.value.returncode == 7
    assert any(r'failed: \xff' in call.args[0] for call in log_stub.call_args_list)


def test_verbose_subprocess_invalid_utf8_success(mocker: pytest_mock.MockerFixture) -> None:
    log_stub = mocker.stub('custom_logger')
    ctx.LOGGER.set(log_stub)
    ctx.VERBOSITY.set(1)
    ctx.run_subprocess([sys.executable, '-c', "import os; os.write(1, b'output: \\xff\\n')"])
    assert any(r'output: \xff' in call.args[0] for call in log_stub.call_args_list)
