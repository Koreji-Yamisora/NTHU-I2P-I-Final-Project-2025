class crd(int):
    """crd."""

    def __new__(cls, value):
        obj = super().__new__(cls, value)
        obj.old = None
        return obj

    def per(self, r):
        """Per."""
        self.old = r
        return crd(self * r // 100)

    def invert(self):
        """Invert."""
        if self.old:
            return crd(self * (100 - self.old) // 100)

    def get(self):
        """Get."""
        return self

    def copy(self):
        """Copy."""
        return crd(self)


if __name__ == '__main__':
    print(crd(100) + 10)
    print(type(crd(100).per(50)))
    print(type(crd(100)))
