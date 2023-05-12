from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as f:
    requirements = f.readlines()

setup(
    name='corregivos',
    version='0.1',
    description='Ayudante para corregir tps de github classroom',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Leo Gassman',
    author_email='lgassman@gmail.com',
    packages=find_packages(),
    install_requires=requirements,
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)