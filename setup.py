from setuptools import setup

setup(
    version="0.2vayana",
    name='python-xlsx',
    description="Tiny python code for parsing data from Microsoft's Office Open XML Spreadsheet format",
    long_description="",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    author='Chris Adams',
    author_email='chris@improbable.org',
    url='http://github.com/acdha/python-xlsx',
    packages=[
        "xlsx"
    ],
    install_requires=[
      'M2Crypto == 0.30.1',
    ],
    zip_safe=False,
    include_package_data=True,
)
