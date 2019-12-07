from setuptools import setup, find_packages

__version__ = '0.0.1'

setup(
    name="lazy-bot-tester",
    version=__version__,
    author="Ros@Ros_1224",
    description="test environment for limit order book",
    install_requires=[
      "websockets",
      "asyncio",
      "numpy",
      "aioredis",
      "aioinflux"
    ],
    entry_points={
      'console_scripts':[
        'lazy-bot-tester-collecter = lazybot.collector.core:main',
      ],
    },
    packages=find_packages(exclude=('tests', 'docs'))
)
