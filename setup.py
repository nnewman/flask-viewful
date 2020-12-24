import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="flask-viewful",
    version="0.0.1",
    author="Neil Newman",
    description='A minimal library for powerful class-based views in Flask',
    long_description=long_description,
    url='https://github.com/nnewman/flask-viewful',
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
)
