from __future__ import annotations

import ast
import re
from cmath import sqrt as csqrt
from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
from math import sqrt
from pprint import pp
from typing import overload

from Scanner import Scanner


class EqualityMember:
    exp: list[float]

    def __init__(self, *args: float) -> None:
        self.exp = [*args]

    @property
    def degree(self):
        return len(self.exp) - 1

    def nullify(self):
        return -self

    def __neg__(self):
        return EqualityMember(*[-1 * x for x in self.exp])

    def __add__(self, other: EqualityMember):
        fac = deepcopy(self.exp)
        pad = deepcopy(other.exp)
        if self.degree > other.degree:
            pad.extend([0.0] * (self.degree - other.degree))
        elif self.degree < other.degree:
            fac.extend([0.0] * (other.degree - self.degree))
        members_sum = [0.0] * (max(self.degree, other.degree) + 1)
        for i, (x, y) in enumerate(zip(fac, pad)):
            members_sum[i] = x + y
        return EqualityMember(*members_sum)

    def __getitem__(self, key: int):
        return self.exp[key]

    def __matmul__(self, key: int) -> float:
        return self.exp[key]

    @overload
    def __eq__(self, other: EqualityMember) -> bool: ...
    @overload
    def __eq__(self, other: object) -> bool: ...

    def __eq__(self, other: object | EqualityMember) -> bool:
        assert type(other) is EqualityMember, (
            "can only compare EqualityMember with EqualityMember"
        )
        for x, y in zip(self.exp, other.exp):
            if x != y:
                return False
        return True

    def __str__(self) -> str:
        if self.degree == 0 and self.exp[0] == 0:
            return "0"
        return " ".join([f"{x:+}*X^{n}" for n, x in enumerate(self.exp)])

    def __repr__(self) -> str:
        return str(self)


class Equation:
    def __init__(self, left: EqualityMember, right: EqualityMember) -> None:
        self.left = left
        self.right = right

    def simplify(self):
        return Equation(self.left + self.right.nullify(), EqualityMember(0))

    def solve(self):
        if self.left == self.right:
            return print("any real number")

        if self.degree == 1:
            return self._solve1()

        if self.degree == 2:
            return self._solve2()

    def _solve1(self):
        print("Solution:", (self.left[0] * -1) / self.left[1])

    def _solve_complex(self, a: float, b: float, d: float):

        def __format_complex(z: complex):
            real = Fraction(Decimal(f"{z.real}"))
            imag = Fraction(Decimal(f"{z.imag}"))
            s = f"{real}"
            s += " + " if z.imag >= 0 else " - "
            s += f"{abs(imag.numerator)}i/{imag.denominator}"
            return s

        d0 = (-b - complex(imag=sqrt(-d))) / (2 * a)
        d1 = (-b + complex(imag=sqrt(-d))) / (2 * a)
        print(__format_complex(d0))
        print(__format_complex(d1))

    def _solve2(self):
        d, a, b, _ = self.discriminant
        if d < 0:
            print("discriminant is strictly negative.")
            self._solve_complex(a, b, d)
        elif d == 0:
            print(f"unique solution: {-(b / (2 * a))}")
        else:
            print("discriminant is strictly positive.")
            print(
                "2 solutions: "
                f"{((-b - sqrt(d)) / (2 * a))} | {((-b + sqrt(d)) / (2 * a))}"
            )

    @property
    def degree(self):
        return max(self.left.degree, self.right.degree)

    @property
    def discriminant(self):
        assert self.right == EqualityMember(0), (
            "can only calculate discriminant on reduced form"
        )
        c, b, a = self.left.exp
        return b**2 - 4 * (a * c), a, b, c

    def __str__(self) -> str:
        return f"{self.left} = {self.right}"

    def __repr__(self) -> str:
        return str(self)


class Parser:
    @staticmethod
    def new_equation_from_string(inp: str) -> Equation:
        first, second = [x.strip() for x in inp.split("=")]

        return Equation(
            Parser.new_member_from_string(first),
            Parser.new_member_from_string(second),
        )

    @staticmethod
    def new_member_from_string(inp: str) -> EqualityMember:
        matches = re.compile(
            r"((?:\+|-)?\s?(?:\d+(?:.\d+)?)\s?)\*(\s?X\^\d)"
        ).findall(inp)
        factors = [0.0] * len(matches)
        for fac, exp in matches:
            x = float(fac.replace(" ", ""))
            i = int(exp.strip().replace("X^", ""))
            factors[i] = x
        return EqualityMember(*factors)


""" f = Parser.new_equation_from_string("1 * X^0 + 2 * X^1 + 5 * X^2 = 0")
r = f.simplify()
print(f"Reduced form: {r}")
print(f"Polynomial degree: {r.degree}")
if r.degree > 2:
    print("The polynomial degree is strictly greater than 2, I can't solve.")
else:
    r.solve() """

s = Scanner("1 * X^0 + 2 * X^1 + 5 * X^2 = 0")
pp(s.lex())
