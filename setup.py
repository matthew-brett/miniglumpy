# miniglumpy setup script
from os.path import join as pjoin

extra_kwargs = {}
try:
    # we don't want to depend on setuptools
    # please don't use any setuptools specific API
    from setuptools import setup
    extra_kwargs = {}
except ImportError:
    from distutils.core import setup

classifiers=[
    'Operating System :: OS Independent',
    'Intended Audience :: Developers',
    "License :: OSI Approved :: BSD License",
    'Natural Language :: English',
    'Programming Language :: Python',
    'Topic :: Software Development']


setup(name='miniglumpy',
      version='0.1',
      description='A very small glumpy fragment',
      long_description="""Glumpy-lite for displaying 2D slices""",
      author='Matthew Brett modifying/copying glumpy by Nicolas P. Rougier',
      author_email='matthew.brett@gmail.com',
      url='http://github.com/matthew-brett/miniglumpy',
      packages=['miniglumpy', 'miniglumpy.gshaders'],
      package_data = {'miniglumpy':
                      [pjoin('gshaders', '*.txt'),
                      ]},
      license='BSD',
      classifiers=classifiers,
      **extra_kwargs)
