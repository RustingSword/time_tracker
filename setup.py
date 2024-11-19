"""Setup file for the time tracker package."""

from setuptools import setup, find_packages

setup(
    name="timetracker",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "matplotlib>=3.5.0",
        "numpy>=1.21.0",
        "pandas>=1.3.0",
        "rich>=10.0.0",
        "pymonctl>=1.0.0",  # Update version as needed
        "pywinctl>=1.0.0",  # Update version as needed
    ],
    entry_points={
        'console_scripts': [
            'track=track:main',
            'analyze=analyze:main',
        ],
    },
    author="RustingSword",
    author_email="i@toonaive.me",
    description="A time tracking application that monitors and analyzes user activity",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    keywords="time tracking, productivity, activity monitor",
    url="https://github.com/RustingSword/time_tracker",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Office/Business :: Time Tracking",
    ],
    python_requires=">=3.8",
)
