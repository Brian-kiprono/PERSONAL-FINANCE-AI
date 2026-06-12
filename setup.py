# setup.py
from setuptools import setup, find_packages

setup(
    name="finance-ai",
    version="2.0.0",
    description="Personal Finance Manager with AI Predictions",
    author="Your Name",
    author_email="your-email@example.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask==2.3.3',
        'Flask-SQLAlchemy==3.1.1',
        'pandas==2.0.3',
        'plotly==5.17.0',
        'scikit-learn==1.3.0',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
    ],
)