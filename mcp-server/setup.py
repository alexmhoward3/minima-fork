from setuptools import setup, find_packages

setup(
    name="minima",
    version="0.0.1",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "mcp-python>=0.1.0",
        "pydantic>=2.0.0",
        "python-dotenv>=0.19.0",
        "langchain>=0.1.0",
        "langchain_community>=0.0.1",
        "sentence-transformers>=2.2.2",
        "transformers>=4.30.0",
        "torch>=2.0.0",
        "qdrant-client>=1.6.0",
        "langchain-qdrant>=0.0.1",
    ],
    python_requires=">=3.10",
)