from setuptools import setup, find_packages

setup(
    name='pyhton_jito_bundle',
    version='0.1',
    packages=find_packages(include=[
        'geyser_grpc_plugin',
        'jito_geyser',
        'jito_searcher_client',
        'jito_searcher_client.*',
        'mev_protos'
    ]),
    install_requires=[
        'solana',
        'solders',
        'spl',
        'grpcio',
        'protobuf',
        'click'
    ],
    package_data={
        '': ['*.py', '*.pyi'],
    },
    include_package_data=True,
)
