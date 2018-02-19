import shutil
import os

shutil.move('MainWindow.py', 'MainWindow.tmp')

with open('MainWindow.tmp', 'rt') as fin:
    with open('MainWindow.py', 'wt') as fout:
        for line in fin:
            fout.write(line.replace('icons/', 'gui/icons/'))

os.remove('MainWindow.tmp')