#include "dependency.h"

static int i = 0;
void c() {
    while (i < 10) {
        c();
        ++i;
    }
}

void a() {
    c();
}
