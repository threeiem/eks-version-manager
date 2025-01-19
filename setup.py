from setuptools import setup, find_packages

setup(
    name="eks-version-manager",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        line.strip()
        for line in open("requirements.txt")
    ],
    entry_points={
        'console_scripts': [
            'eks-versions=eks_versions:main',
        ],
    },
)
