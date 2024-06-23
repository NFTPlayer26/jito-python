from setuptools import setup, find_packages

setup(
    name='pyhton_jito_bundle',
    version='0.1',
    packages=find_packages(include=[
        "jito_geyser", "jito_geyser.*",
        "jito_searcher_client", "jito_searcher_client.*",
        "mev-protos", "mev-protos.*"
    ]),
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
