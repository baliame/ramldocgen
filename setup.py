from setuptools import *

description = 'Python based command line interface tool for generating HTML content from RAML documentation.'

setup(
    name='ramldocgen',
    version='1.0.2',
    description=description,
    long_description=description,
    url='https://github.com/baliame/ramldocgen',
    author='Baliame',
    author_email='akos.toth@cheppers.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Documentation',
        'Topic :: Software Development :: Documentation',
        'Topic :: Utilities',
    ],
    keywords='raml api documentation generator',
    packages=find_packages(),
    install_requires=[
        "pyraml-parser",
        "click"
    ],
    entry_points={
        'console_scripts': [
            'ramldocgen=ramldocgen.ramldocgen:cli',
        ],
    }
)
