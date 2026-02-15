"""
Setup configuration for Claude Monitoring System
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / 'docs' / 'README.md'
long_description = readme_file.read_text(encoding='utf-8') if readme_file.exists() else ''

# Read requirements
requirements_file = Path(__file__).parent / 'requirements.txt'
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding='utf-8').splitlines()
        if line.strip() and not line.startswith('#')
    ]

setup(
    name='claude-monitoring-system',
    version='1.0.0',
    description='Advanced monitoring and analytics dashboard for Claude AI memory system',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='TechDeveloper',
    author_email='',
    url='https://github.com/yourusername/claude-monitoring-system',
    license='MIT',

    # Package configuration
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,

    # Dependencies
    install_requires=requirements,
    python_requires='>=3.8',

    # Entry points
    entry_points={
        'console_scripts': [
            'claude-monitoring=run:main',
        ],
    },

    # Classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Framework :: Flask',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Monitoring',
    ],

    # Additional metadata
    keywords='claude ai monitoring dashboard analytics flask',
    project_urls={
        'Documentation': 'https://github.com/yourusername/claude-monitoring-system/docs',
        'Source': 'https://github.com/yourusername/claude-monitoring-system',
        'Tracker': 'https://github.com/yourusername/claude-monitoring-system/issues',
    },
)
