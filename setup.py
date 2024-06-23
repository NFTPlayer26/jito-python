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
        # asyncio'nun burada olması gerekmiyor çünkü Python'ın standart kütüphanesinin bir parçası
    ],
    package_data={
        '': ['*.py', '*.pyi'],
    },
    include_package_data=True,
)
