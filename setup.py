from setuptools import setup, find_packages

setup(
    name='pyhton_jito_bundle',
    version='0.1',
    packages=find_packages(where="."),  # include all packages in the project
    package_dir={"": "."},  # root directory as the base
    install_requires=[
        'solana',
        'solders',
        'spl',
        'grpcio',
        'protobuf',
        'click',
        'asyncio',
    ],
)
