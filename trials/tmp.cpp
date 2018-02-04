#include <iostream>
using namespace std;

namespace imp {
    int addition(int x, int y) {
        return x + y;
    }

    void f() {
        addition(2, 3);
    }
}

int addition(int a, int b) {
    int r;
    r = a + b;
    return r;
}

int main() {
    int z = addition(5, 3);
    int q = addition(5, 5);
    cout << "First result:  " << z << "\n";
    cout << "Second result: " << q << "\n";
}
