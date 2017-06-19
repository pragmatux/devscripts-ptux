from setuptools import setup, find_packages

setup(
    name='ptuxrepo',
    version='0.1',
    description='Pragmatux APT repository manager',
    author='Ryan Kuester',
    author_email='pragmatux-users@lists.pragmatux.org',
    license='GPL',
    packages=find_packages(exclude=['tests']),
    install_requires=['docopt', 'debian', 'yaml'],
    entry_points={ 'console_scripts': ['ptuxrepo=ptuxrepo.cli:main'] }
)
