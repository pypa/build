import os

import nox


nox.options.sessions = ['mypy', 'test']
nox.options.reuse_existing_virtualenvs = True


@nox.session(python='3.8')
def mypy(session):
    session.install('.', 'mypy')

    session.run('mypy', '-p', 'build')
    session.run('mypy', '--py2', '-p', 'build')


@nox.session(python=['2.7', '3.5', '3.6', '3.7', '3.8', 'pypy2', 'pypy3'])
def test(session):
    htmlcov_output = os.path.join(session.virtualenv.location, 'htmlcov')
    xmlcov_output = os.path.join(session.virtualenv.location, f'coverage-{session.python}.xml')

    session.install('.', 'importlib_metadata')
    session.install('pytest', 'pytest-cov', 'pytest-mock')

    session.run('pytest', '--cov',
                f'--cov-report=html:{htmlcov_output}',
                f'--cov-report=xml:{xmlcov_output}',
                'tests/', *session.posargs)
