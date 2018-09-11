import os
import shutil
from os import path
from setuptools import setup, find_packages, Command

here = path.abspath(path.dirname(__file__))
remove_dir = ['build', 'dist']

def rmdir():
    for directory in os.listdir(here):
        if directory in remove_dir or directory.endswith('egg-info'):
            dir_path = os.path.join(here, directory)
            if not os.path.isfile(dir_path):
                shutil.rmtree(os.path.join(here, directory))


class Clean(Command):
    description = "Cleaning the project"
    user_options = [('foo=', None, 'Specify the foo to bar.')]

    def initialize_options(self):
        self.foo = None

    def finalize_options(self):
        assert self.foo in (None, 'Foo'), 'Invalid foo!'

    def run(self):
        rmdir()
        print("cleaning complete")


class Rebuild(Command):
    description = "Rebuilding the project"
    user_options = [('foo=', None, 'Specify the foo to bar.')]

    def initialize_options(self):
        self.foo = None

    def finalize_options(self):
        assert self.foo in (None, 'Foo'), 'Invalid foo!'

    def run(self):
        rmdir()
        command = "cd {} & python setup.py install & pause".format(here)
        os.system(command)

        print("rebuild complete")

setup(name='Crawler',
      version='1.0.0',
      author='Dragan Matesic, Zagreb, Croatia',
      packages=find_packages(exclude=['contrib', 'docs', 'tests']),
      install_requires=['requests', 'bs4'],
      cmdclass={'clean': Clean,
                'rebuild': Rebuild}
)