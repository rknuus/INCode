void f() {}

class B {
public:
    B() {
        f();
        m();
    }

    ~B() {
        f();
        m();
    }

    // TODO(KNR): copy c'tor, assignment op, move stuff

    void m() {
        f();
        p();
    }

private:
    void p() {}
};
