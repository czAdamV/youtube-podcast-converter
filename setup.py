from setuptools import setup, find_packages


setup(
    name='ytfeed',
    version='0.1',
    author='Adam Volek',
    author_email='volekada@fit.cvut.cz',
    license='MIT',
    url='https://github.com/czAdamV/youtube-podcast-converter',
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[
        'google-api-python-client',
        'feedgen',
        'requests',
        'ffmpeg-python',
        'flask',
        'pytube3',
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-recording',
            'vcrpy',
        ],
    },
    zip_safe=False,
)
