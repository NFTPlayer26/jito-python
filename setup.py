from setuptools import setup, find_packages

setup(
    name='pyhton_jito_bundle',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'solana',
        'solders',
        'aiogram',
        'aiohttp',
        'logging',
        'asyncstdlib',
        'borsh-construct',
        'construct',
        'spl-token',
        'websockets',
        'emoji',
        'jito_searcher_client'
    ],
    package_data={
        '': ['*.py', '*.pyi'],
    },
    include_package_data=True,
)
