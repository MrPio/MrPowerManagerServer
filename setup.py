from distutils.core import setup
import py2exe

setup(
    name='MrPowerManagerServer',
    version='1.5.2',
    console=['mr_power_manager.py'],
    url='https://github.com/MrPio/MrPowerManagerServer',
    license='CC0 1.0',
    author='MrPio',
    author_email='valeriomorelli50@gmail.com',
    description='Server for the app MrPowerManager which is a toolkit, it gives the user a lot of possibility to remotely control its PCs. '
)
