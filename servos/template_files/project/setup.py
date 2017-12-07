# -*- coding: utf-8 -*-
from setuptools import setup

setup(
    setup_requires=['nose>=1.0', 'pbr>=1.8'],
    test_suite='nose.collector',
    pbr=True
)
