import os

from setuptools import setup, find_packages


here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()


requires = ['reg',
            'ply']


# tests_require = ['nose',
#                  'coverage']


setup(name='ledgerbeans',
      version='0.1a0',
      description='Double-entry accounting',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Environment :: Console",
          "Intended Audience :: Financial and Insurance Industry",
          "Programming Language :: Python :: 3.4",
          "Topic :: Office/Business :: Financial :: Accounting",
      ],
      author='Olaf Conradi',
      author_email='olaf@conradi.org',
      url='https://github.com/oohlaf/ledgerbeans',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      entry_points={
          'console_scripts': [
              'ledgerbeans = ledgerbeans.main:main',
              ]
          }
      )
