from setuptools import setup, find_packages

setup(
    name='devscripts-ptux',
    version='0.1',
    description='Pragmatux development halper scripts',
    author='Ryan Kuester',
    author_email='pragmatux-users@lists.pragmatux.org',
    license='GPL',
    py_modules=['ptuxversion'],
    install_requires=['docopt'],
    entry_points={ 'console_scripts': ['ptuxversion=ptuxversion:cli'] }
)
