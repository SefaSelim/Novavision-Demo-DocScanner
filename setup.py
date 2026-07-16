import setuptools

setuptools.setup(
    name="docscanner",
    version="0.0.1",
    author="DigiNova",
    author_email='info@diginova.com.tr',
    description="DocScanner",
    url='https://github.com/novavision-ai/docscanner',
    license='MIT',
    install_requires=['sdk', 'opencv-python-headless', 'numpy'],

    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],

    packages=[
        'novavision.docscanner',
        'novavision.docscanner.executors',
        'novavision.docscanner.models',
        'novavision.docscanner.utils',
    ],
    package_dir={'novavision.docscanner': 'src'},
    python_requires=">=3.6"
)