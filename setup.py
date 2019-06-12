import io
import os
import re
from setuptools import setup, find_packages


def read(filename):
    filename = os.path.join(os.path.dirname(__file__), filename)
    text_type = type(u"")
    with io.open(filename, mode="r", encoding='utf-8') as fd:
        return re.sub(text_type(r':[a-z]+:`~?(.*?)`'), text_type(r'``\1``'), fd.read())


setup(
    name="erc20bank-cli",
    version="0.3dev",
    url="https://github.com/ideal-money/",
    license='BSD 2-Clause License',

    author="Siftal",

    description="Command line interfaces to work with erc20bank, oracles and liquidator smart contracts",
    long_description=read("README.md"),

    python_requires='>=3.6',

    packages=find_packages(),

    install_requires=[
        "web3",
        "click",
        "asn1crypto",
        "cffi",
        "pysha3"
    ],

    entry_points={
        'console_scripts': [
            'erc20bank = erc20bank_cli.erc20bank:main',
            'oracles = erc20bank_cli.oracles:main',
            'liquidator = erc20bank_cli.liquidator:main'
        ]
    },

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)

if os.path.exists(os.path.expanduser('~/.erc20bank.json')):
    os.remove(os.path.expanduser('~/.erc20bank.json'))
