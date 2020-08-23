import setuptools

with open("README.md", "r") as fh: long_description = fh.read()

setuptools.setup(
    name="multisource_args_mmd", # Replace with your own username
    version="0.0.1",
    author="Matthew McDermott",
    author_email="mattmcdermott8@gmail.com",
    description="A utility for abstracting args across interfaces and reading/writing them to config files.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mmcdermott/multisource_args",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
