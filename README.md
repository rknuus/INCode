# INCode
Interactive diagram generator from C++ code. Combine human intelligence to select only relevant elements for a diagram with machine to perform call tree analysis in correct and repetitive manner.

## Dependencies
```bash
$ sudo apt install python3-setuptools -y
$ sudo apt install python3-pip -y
$ pip3 install pyqt5
$ sudo apt install libclang-6.0-dev -y
```

## Dev Setup
```bash
$ cd ~/workspace
$ git clone https://github.com/rknuus/INCode.git
$ cd INCode
$ sudo python3 setup.py develop
$ LD_LIBRARY_PATH=/usr/lib/llvm-6.0/lib python3 setup.py test
$ LD_LIBRARY_PATH=/usr/lib/llvm-6.0/lib python3 INCode/bin/INCode
```
