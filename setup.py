from setuptools import find_packages, setup, Command

# https://github.com/pypa/pypi-legacy/issues/148
try:
    import pypandoc
    LONG_DESCRIPTION = pypandoc.convert('README.md', 'rst')
except ImportError:
    LONG_DESCRIPTION = open('README.md').read()

setup(
    name='whatabanger',
    version='1.0.0',
    description='A Bit Banged (via PyFTDI) based SWD implementation',
    long_description=LONG_DESCRIPTION,
    author='Peter Adkins',
    author_email='peter.adkins@kernelpicnic.net',
    url='https://www.github.com/darkarnium/whatabanger',
    packages=find_packages('src'),
    license='MIT',
    download_url='',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    package_dir={
        'whatabanger': 'src/whatabanger',
    },
    scripts=[
        'src/swdinit.py'
    ],
    setup_requires=[
        'pytest-runner',
    ],
    tests_require=[
        'pytest',
        'pytest-cov',
    ],
    install_requires=[
        'pyftdi==0.29.2',
    ]
)
