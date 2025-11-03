#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup

with open("requirements.txt") as requirements_file:
    requirements = [line.strip() for line in requirements_file if line.strip()]

setup(
    name="keep_diverse",
    version="1.0.0",
    author="L3odr0id",
    packages=["keep_diverse"],
    install_requires=requirements,
)
