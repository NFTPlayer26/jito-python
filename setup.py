from setuptools import setup, find_packages

setup(
    name='pyhton_jito_bundle',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'solana',
        'solders',
        'spl',
        'grpcio',
        'protobuf',
        'click',
        'asyncio',  # Bu, Python'ın standart kütüphanesinin bir parçası olduğu için aslında gereksinimlerde olmamalıdır.
    ],
)
