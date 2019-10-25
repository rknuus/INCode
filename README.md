# INCode
Interactive diagram generator from C++ code. Combine human intelligence to select only relevant elements for a diagram with machine to perform call tree analysis in correct and repetitive manner.

## Dependencies

### Using a stretch container
If you're using a stretch container, you have to add the repository for the right libclang version first:
```bash
sudo apt install -y software-properties-common
wget --no-check-certificate -O - https://apt.llvm.org/llvm-snapshot.gpg.key | sudo apt-key add -
sudo apt-add-repository "deb http://apt.llvm.org/stretch/ llvm-toolchain-stretch-6.0 main"
sudo apt update
```

### Install Dependencies
```bash
sudo apt install -y python3-setuptools python3-pip python3-pyqt5 libclang-6.0-dev
```

## Build Project
```bash
cd ~/workspace
git clone https://github.com/rknuus/INCode.git
cd INCode
sudo python3 setup.py install
sudo python3 setup.py build
build/scripts-3.5/INCode
```

## Dev Setup
```bash
cd ~/workspace
git clone https://github.com/rknuus/INCode.git
cd INCode
sudo python3 setup.py develop
LD_LIBRARY_PATH=/usr/lib/llvm-6.0/lib python3 setup.py test
```

## Usage

Start INCode: `LD_LIBRARY_PATH=/usr/lib/llvm-6.0/lib python3 INCode/bin/INCode`

### Entry Dialog
The first window that will popup is the entry dialog. The purpose of this window is to select your starting point.

At first, you have to select the [compilation database (json)](https://clang.llvm.org/docs/JSONCompilationDatabase.html) of the c++ code you want to analyze.

Afterwards, all cpp files from the project should show up. From this list you can choose your wanted entry file.

Once that is done, you should be able to see all callables from the entry file, from where you can select entry point and click `OK`.

### Diagram Configuration
The diagram configuration window shows up right after the selection of the entry point and is the main window of this application.

Your entry point is the root of the tree view. From there you can start to reveal the child callables from the functions.
The reveal of the root node is already done by the application. Now you can either go to `Actions -> Reveal Children` or just use the shortcut `Ctrl + R`.

Every node has a checkbox that you have to check for every callable that you'd like to include into the diagram (shortcut: `Space`).

With the Option `Show Preview` (shortcut: `Ctrl + T`) on the Actions tab you can enable and disable a preview of the current state of the diagram.

As soon as you have every wanted callable checked, you can export the diagram using `Actions -> Export` (shortcut `Ctrl + S`).

#### Export
After the export function of the diagram configuration window you should see the export output in the console.
You can copy the content into a file and then the following command:
`plantuml <file>`

After that the UML diagram should be generated as `<file>.png`.


