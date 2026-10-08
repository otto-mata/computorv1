from __future__ import annotations

import readline  # noqa: F401
import sys
from decimal import Decimal
from fractions import Fraction
from math import isqrt
from typing import overload

from Parser import Expr, TokenType
from Scanner import Input, Simplifyer, Triplet, XVar, classname


class EqualityMember:
    parts: list[XVar]

    def __init__(self, parts: list[XVar]) -> None:
        self.parts = parts

    def copy(self):
        return EqualityMember(
            [p.copy() for p in self.parts],
        )

    @property
    def degree(self):
        deg = 0
        for i, v in enumerate(self.parts):
            if v.fac != 0:
                deg = i
        return deg

    @property
    def _cdeg(self):
        """degree including null factors"""
        return len(self.parts) - 1

    def _reduce_factors(self) -> list[float]:
        return [p.fac for p in self.parts]

    def _iadd_xvar(self, e: XVar):
        if self._cdeg < e.degree:
            self.parts += [
                XVar(fac=0, degree=i) for i in range(self._cdeg + 1, e.degree)
            ]
            self.parts += [e]
        else:
            self.parts[e.degree] += e
        return self

    def _iadd_em(self, em: EqualityMember):
        for i, v in enumerate(em.parts):
            self.parts[i] += v
        return self

    @overload
    def __iadd__(self, other: EqualityMember): ...
    @overload
    def __iadd__(self, other: XVar): ...
    def __iadd__(self, other: object):
        if isinstance(other, XVar):
            return self._iadd_xvar(other)
        if isinstance(other, EqualityMember):
            return self._iadd_em(other)
        raise TypeError(
            "Can only add XVar and EqualityMember to EqualityMember"
        )

    @overload
    def __add__(self, other: EqualityMember): ...
    @overload
    def __add__(self, other: XVar): ...
    def __add__(self, other: object):
        if isinstance(other, (XVar, EqualityMember)):
            em = self.copy()
            em += other
            return em
        raise TypeError(
            "Can only add XVar and EqualityMember to EqualityMember"
        )

    def __str__(self) -> str:
        s = []
        for i, p in enumerate(self.parts):
            if p.fac == 0 and p.degree > 0:
                continue
            if p.is_neg and i > 0:
                s.append("-")
            elif i > 0:
                s.append("+")
            x = abs(p) if i > 0 else p
            s.append(f"{x}")
        return " ".join(s)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, EqualityMember):
            if self.degree != other.degree:
                return False
            for sp, op in zip(self.parts, other.parts):
                if sp != op:
                    return False
            return True

        if isinstance(other, (float, int)):
            if self.degree != 0:
                return False
            return self.parts[0] == other
        return False

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __neg__(self):
        return EqualityMember(
            [-p for p in self.parts],
        )


class Equation:
    left: EqualityMember
    right: EqualityMember
    reduced: Equation

    def __init__(self) -> None:
        pass

    def copy(self) -> Equation:
        eq = Equation()
        eq.left = self.left.copy()
        eq.right = self.right.copy()
        return eq

    @property
    def degree(self):
        return self.reduced.left.degree

    @property
    def discriminant(self):
        return self.b**2 - 4 * (self.a * self.c)

    @property
    def a(self):
        if self.degree >= 2:
            return self.reduced.left.parts[2].fac
        return 0

    @property
    def b(self):
        if self.degree >= 1:
            return self.reduced.left.parts[1].fac
        return 0

    @property
    def c(self):
        return self.reduced.left.parts[0].fac

    @classmethod
    def _flatten_r(
        cls,
        expr: object,
    ) -> list[float | XVar]:
        if isinstance(expr, Triplet):
            l_fse = cls._flatten_r(expr.left)
            r_fse = cls._flatten_r(expr.right)
            return l_fse + r_fse
        if isinstance(expr, (float, XVar)):
            return [expr]
        raise RuntimeError(expr)

    @classmethod
    def _flatten_simplified_equation(
        cls,
        expr: object,
    ) -> tuple[list[float | XVar], list[float | XVar]]:
        if not isinstance(expr, Triplet) or expr.op != TokenType.EQUAL:
            raise TypeError(f"Invalid equation (got {expr})")

        l_fse = cls._flatten_r(expr.left)
        r_fse = cls._flatten_r(expr.right)
        return (l_fse, r_fse)

    @classmethod
    def _group_parts_in_member(
        cls,
        member: list[float | XVar],
    ) -> list[XVar]:
        degree_sums = [0.0]
        for e in member:
            if isinstance(e, float):
                degree_sums[0] += e
            if isinstance(e, XVar):
                if len(degree_sums) < int(e.degree + 1):
                    degree_sums += [0.0] * (
                        int(e.degree + 1) - len(degree_sums)
                    )
                degree_sums[e.degree] += e.fac
        return [XVar(fac=v, degree=i) for i, v in enumerate(degree_sums)]

    @staticmethod
    def create_from(expr: Expr):
        eq = Equation()
        se = Simplifyer().exec(expr)
        l_flat, r_flat = Equation._flatten_simplified_equation(se)
        l_grp, r_grp = (
            Equation._group_parts_in_member(l_flat),
            Equation._group_parts_in_member(r_flat),
        )
        eq.left = EqualityMember(l_grp)
        eq.right = EqualityMember(r_grp)

        if eq.left.degree < eq.right.degree:
            eq.left += XVar(degree=eq.right.degree, fac=0)
        elif eq.right.degree < eq.left.degree:
            eq.right += XVar(degree=eq.left.degree, fac=0)
        eq._reduce()
        return eq

    def __str__(self) -> str:
        return f"{self.left} = {self.right}"

    def _reduce(self) -> Equation:
        self.reduced = self.copy()
        self.reduced.left += -self.reduced.right
        self.reduced.right += -self.reduced.right
        return self.reduced

    def solve(self):
        print(f"Reduced form: {self.reduced}")
        if self.degree == 0 and self.left != self.right:
            print("No solution")
            return
        print(f"Polynomial degree: {self.degree}")
        if self.left == self.right:
            print("Any real number is a solution")
            return
        if self.degree == 1:
            self._solve1()
            return
        if self.degree == 2:
            self._solve2()
            return
        raise ValueError(
            "The polynomial degree is strictly greater than 2, I can't solve"
        )

    def _solve1(self):
        print("The solution is:")
        print(-self.c / self.b)

    def _solve_complex(self):

        def __format_complex(z: complex):
            sl = []
            real = Decimal(f"{z.real}")
            imag = Decimal(f"{z.imag}")
            if real != 0:
                sl.append(f"{real}")
            sl.append(f"± {imag}i")
            return " ".join(sl)

        if self.c != 0 and self.b == 0:
            ...
        d0 = (-self.b + complex(imag=(-self.discriminant) ** 0.5)) / (
            2 * self.a
        )
        print(__format_complex(d0))

    def _solve2(self):
        d = self.discriminant
        if d < 0:
            print(
                "Discriminant is strictly negative, "
                "the two complex solutions are:"
            )
            self._solve_complex()
        elif d == 0:
            print(f"The solution is:\n{-(self.b / (2 * self.a))}")
        else:
            print("Discriminant is strictly positive, the two solutions are:")
            if self.c != 0 and self.b == 0:
                if isqrt(int(abs(self.c))) ** 2 == abs(self.c):
                    print(f"±{abs(self.c) ** 0.5}")
                else:
                    print(f"±√{abs(self.c)}")
            else:
                d0 = (-self.b + (d**0.5)) / (2 * self.a)
                d1 = (-self.b - (d**0.5)) / (2 * self.a)
                if d0 == 0:
                    d0 = abs(d0)
                if d1 == 0:
                    d1 = abs(d1)
                print(Decimal(f"{d0:.6}"))
                print(Decimal(f"{d1:.6}"))


def main(argc: int, argv: list[str]):
    try:
        if argc == 1:
            expr = Input().get().parse()
        else:
            expr = Input().string(argv[1]).parse()
        eq = Equation.create_from(expr)
        eq.solve()
    except (RuntimeError, ValueError) as e:
        print(f"got {classname(e)} -> {e}")
    except (EOFError, KeyboardInterrupt):
        print("\nexiting")
        return


if __name__ == "__main__":
    main(len(sys.argv), sys.argv)
