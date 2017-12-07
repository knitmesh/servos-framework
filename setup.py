# -*- coding: utf-8 -*-
from setuptools import setup

setup(
    setup_requires=['nose>=1.0', 'pbr>=1.8'],
    test_suite='nose.collector',
    package_data={
        '': ['locale/en/LC_MESSAGES/*.mo', 'locale/zh_CN/LC_MESSAGES/*.mo'],
    },
    pbr=True
)
