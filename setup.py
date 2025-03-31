from setuptools import setup, find_packages

setup(
    name='RefineDLC',
    version='0.1.0',
    description='refineDLC: Advanced Post-Processing Pipeline for DeepLabCut Outputs',
    author='Weronika Klecel, Hadley Rahael and Samantha A. Brooks',
    packages=find_packages(),
    install_requires=[
        'pandas',
        'numpy',
        'scipy',
        'matplotlib'
    ],
    entry_points={
        'console_scripts': [
            'refinedlc-clean=refindlc.clean_coordinates:main',
            'refinedlc-likelihood=refindlc.likelihood_filter:main',
            'refinedlc-position=refindlc.position_filter:main',
            'refinedlc-interpolate=refindlc.interpolate:main'
        ]
    },
)
