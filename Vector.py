from __future__ import annotations

from typing import Iterable


class Vector(list):

    def __mul__(self, other) -> Vector:
        if isinstance(other, Iterable):
            return Vector((self[i]*n for i, n in enumerate(other)))
        return Vector((n*other for n in self))

    def __truediv__(self, other) -> Vector:
        if isinstance(other, Iterable):
            return Vector((self[i]/n for i, n in enumerate(other)))
        return Vector((n/other for n in self))

    def __floordiv__(self, other) -> Vector:
        if isinstance(other, Iterable):
            return Vector((self[i]//n for i, n in enumerate(other)))
        return Vector((n//other for n in self))

    def __add__(self, other) -> Vector:
        if isinstance(other, Iterable):
            return Vector((self[i]+n for i, n in enumerate(other)))
        return Vector((n+other for n in self))

    def __sub__(self, other) -> Vector:
        if isinstance(other, Iterable):
            return Vector((self[i]-n for i, n in enumerate(other)))
        return Vector((n-other for n in self))

    def __lt__(self, other):
        if isinstance(other, Iterable):
            for i, n in enumerate(other):
                if not (self[i] < n):
                    return False
            return True
        return sum(self) < other

    def __gt__(self, other):
        if isinstance(other, Iterable):
            for i, n in enumerate(other):
                if not (self[i] > n):
                    return False
            return True
        return sum(self) > other

    def __eq__(self, other):
        if isinstance(other, Iterable):
            for i, n in enumerate(other):
                if not (self[i] == n):
                    return False
            return True
        return sum(self) == other

    def __ne__(self, other):
        if isinstance(other, Iterable):
            for i, n in enumerate(other):
                if not (self[i] != n):
                    return False
            return True
        return sum(self) != other

    def __ge__(self, other):
        if isinstance(other, Iterable):
            for i, n in enumerate(other):
                if not (self[i] >= n):
                    return False
            return True
        return sum(self) >= other

    def __le__(self, other):
        if isinstance(other, Iterable):
            for i, n in enumerate(other):
                if not (self[i] <= n):
                    return False
            return True
        return sum(self) <= other

    def __str__(self):
        return 'V'+super(list, self).__str__()

    def __round__(self, n=None):
        return Vector((round(num, n) for num in self))
