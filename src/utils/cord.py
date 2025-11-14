class crd(int):
    def __new__(cls, value):
        obj = super().__new__(cls, value)
        obj.old = None
        return obj

    def per(self, r):
        self.old = r
        return crd(self * r // 100)

    def invert(self):
        if self.old:
            return crd(self * (100 - self.old) // 100)

    def get(self):
        return self

    def copy(self):
        return crd(self)


if __name__ == "__main__":
    print(crd(100) + 10)
    print(type(crd(100).per(50)))
    print(type(crd(100)))
