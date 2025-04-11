from setuptools import setup, find_packages

setup(
    name="tabtabtab-lib",
    version="0.1.0",
    packages=find_packages(),
    author="TabTabTabAI",  # Assuming author name
    author_email="",  # Placeholder
    description="Core library for TabTabTab functionality.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/tabtabtabai/tabtabtab-lib",  # Repository URL
    # Add any dependencies here if needed, e.g., install_requires=['requests']
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",  # Choose appropriate license
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
)
