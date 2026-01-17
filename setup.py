from setuptools import setup, find_packages

setup(
    name="indian_vedic_jyotish",
    version="0.1.0",
    description="A Python library for accurate Indian Astrology calculations, focusing on Drik Siddhanta and Bengali Panjika rules.",
    author="Rakesh",
    author_email="rakesh@example.com",
    packages=find_packages(),
    install_requires=[
        "pyswisseph>=2.10.3.2",
        "pytz>=2023.3",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
