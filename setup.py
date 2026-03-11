from setuptools import setup, find_packages
import os

# Read the contents of README file
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="nixagent",
    version="1.17",
    description="A sophisticated AI agent toolkit supporting multiple AI providers with tool calling capabilities, enterprise state management, HITL, Graph routing, LangChain support, and structured outputs.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="TechnicalHeist",
    author_email="contact@technicalheist.com",
    url="https://technicalheist.com",
    project_urls={
        "Bug Reports": "https://github.com/technicalheist/nixagent/issues",
        "Source": "https://github.com/technicalheist/nixagent",
    },
    packages=find_packages(include=["nixagent", "nixagent.*"]),
    py_modules=["app"],
    install_requires=[
        "python-dotenv>=0.19.0",
        "requests>=2.25.0"
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
        ],
    },
    entry_points={
        "console_scripts": [
            "local-agent=app:main",
        ]
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="ai agent toolkit ollama openai tool-calling automation",
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
    python_requires=">=3.8",
    zip_safe=False,
)
