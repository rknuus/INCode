#include "dependency.h"

void c() {}

void a() {
    c();
}
