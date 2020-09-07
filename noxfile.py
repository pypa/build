import os
import os.path
import tempfile

import nox


nox.options.sessions = ['mypy', 'test']
nox.options.reuse_existing_virtualenvs = True


@nox.session(python='3.8')
def mypy(session):
    session.install('.', 'mypy')

    session.run('mypy', 'src/build')
    session.run('mypy', '--py2', 'src/build')


def run_tests(session, env=None):
    htmlcov_output = os.path.join(session.virtualenv.location, 'htmlcov')
    xmlcov_output = os.path.join(session.virtualenv.location, f'coverage-{session.python}.xml')

    session.run('pytest', '--cov', '--cov-config', 'setup.cfg',
                f'--cov-report=html:{htmlcov_output}',
                f'--cov-report=xml:{xmlcov_output}',
                'tests/', *session.posargs, env=env)


@nox.session(python=['2.7', '3.5', '3.6', '3.7', '3.8', 'pypy2', 'pypy3'])
def test(session):
    session.install('.[test]')
    run_tests(session)


@nox.session(python=['2.7', '3.5', '3.6', '3.7', '3.8', 'pypy2', 'pypy3'])
def test_pythonpath(session):
    session.install('-r', 'requirements-dev.txt')
    run_tests(session, env={'PYTHONPATH': 'src'})


@nox.session(python=['2.7', '3.5', '3.6', '3.7', '3.8', 'pypy2', 'pypy3'])
def test_wheel(session):
    session.install('-r', 'requirements-dev.txt')

    with tempfile.TemporaryDirectory(prefix='python-build-wheel-') as dest:
        session.run(
            'python', '-m', 'build', '--wheel', '--no-isolation', '--outdir', dest,
            env={'PYTHONPATH': 'src'}
        )
        for target in os.listdir(dest):
            if target.endswith('.whl'):
                session.install(os.path.join(dest, target))
                break

    run_tests(session)


@nox.session(python=['2.7', '3.5', '3.6', '3.7', '3.8', 'pypy2', 'pypy3'])
def test_sdist(session):
    session.install('-r', 'requirements-dev.txt')

    with tempfile.TemporaryDirectory(prefix='python-build-wheel-') as dest:
        session.run(
            'python', '-m', 'build', '--sdist', '--no-isolation', '--outdir', dest,
            env={'PYTHONPATH': 'src'}
        )
        for target in os.listdir(dest):
            if target.endswith('.tar.gz'):
                session.install(os.path.join(dest, target))

    run_tests(session)
