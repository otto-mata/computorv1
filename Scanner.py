from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from token import ENCODING
from tokenize import tokenize

from Parser import (
    BinOp,
    Expr,
    ExprVisitor,
    Grouping,
    Number,
    Parser,
    Token,
    TokenType,
    UnOp,
    Variable,
)


def classname(o: object) -> str:
    return o.__class__.__name__


class Scanner:
    src: str

    def __init__(self, src: str) -> None:
        self.src = src

    def lex(self) -> list[Token]:
        return [
            Token.from_token_info(t)
            for t in tokenize(BytesIO(self.src.encode()).readline)
            if t.type != ENCODING
        ]


class Printer(ExprVisitor[str]):
    level: int

    def __init__(self) -> None:
        super().__init__()
        self.level = 0

    def parenthesize(self, name: str, *expressions: Expr) -> str:
        self.level += 1
        s: str = f"[{self.level}]"
        s += "(" + name
        for expr in expressions:
            s += " " + expr.accept(self)
        self.level -= 1
        s += ")"
        return s

    def visit_unary(self, node: UnOp) -> str:
        return self.parenthesize(node.op.lexeme, node.right)

    def visit_number(self, node: Number) -> str:
        return f"n:{node.value}"

    def visit_variable(self, node: Variable) -> str:
        return f"v:{node.name.lexeme}"

    def visit_binary(self, node: BinOp) -> str:
        return self.parenthesize(node.op.lexeme, node.left, node.right)

    def visit_grouping(self, node: Grouping) -> str:
        return self.parenthesize("group", node.expression)

    def print(self, expression: Expr) -> None:
        self.level = 0
        print(expression.accept(self))


class XVar:
    is_neg: bool
    degree: int
    fac: float

    def __init__(self, degree: int = 0, fac: float = 1.0) -> None:
        self.degree = degree
        self.fac = fac
        self.is_neg = fac < 0

    def copy(self):
        return XVar(
            degree=self.degree,
            fac=self.fac,
        )

    def __str__(self) -> str:
        # if self.degree == 0:
        #     return f"{self.fac}"
        # if self.fac == 1:
        #     return f"X^{self.degree}"
        return f"{self.fac} * X^{self.degree}"

    def __repr__(self) -> str:
        return str(self)

    def __neg__(self):
        x = self.copy()
        x.is_neg = not x.is_neg
        x.fac = -x.fac
        return x

    def __add__(self, other: XVar) -> XVar:
        if self.degree != other.degree:
            raise ValueError("Cannot add XVar of different degree")
        val = self.fac + other.fac
        return XVar(
            fac=val,
            degree=self.degree,
        )

    def __eq__(self, other: object) -> bool:
        if isinstance(other, XVar):
            return self.fac == other.fac and self.degree == other.degree
        if isinstance(other, (float, int)):
            return self.fac == other and self.degree == 0
        return False

    def __ne__(self, other: object) -> bool:
        return not self == other

    def __sub__(self, other: XVar) -> XVar:
        return self + -other

    def __abs__(self) -> XVar:
        return XVar(fac=abs(self.fac), degree=self.degree)

    def __gt__(self, other: object) -> bool:
        if isinstance(other, XVar):
            return self.fac > other.fac and self.degree == other.degree
        if isinstance(other, (float, int)):
            return self.fac > other and self.degree == 0
        return False


@dataclass
class Triplet:
    left: object
    op: TokenType
    right: object


class Simplifyer(ExprVisitor[object]):
    level: int

    def __init__(self) -> None:
        super().__init__()
        self.level = 0

    def _handle_pow(self, l: object, r: object) -> float | XVar:
        if isinstance(l, XVar) and isinstance(r, float):
            l.degree = int(r)
            return l
        if isinstance(l, float) and isinstance(r, float):
            return l**r
        raise TypeError(
            f"Expected float, got {classname(r)}",
        )

    def _handle_mul(self, l: object, r: object):
        if isinstance(r, XVar) and isinstance(l, float):
            r.fac = l
            return r
        if isinstance(l, XVar) and isinstance(r, float):
            l.fac = r
            return l
        if isinstance(l, float) and isinstance(r, float):
            return l * r
        if isinstance(l, Triplet) and isinstance(r, float):
            l.left = self._handle_mul(l.left, r)
            l.right = self._handle_mul(l.right, r)
            return l
        raise TypeError(
            f"\nl:{classname(l)} {l!r}\nr:{classname(r)} {r!r}",
        )

    def _handle_add_sub(self, l: object, r: object, op: TokenType) -> object:

        if isinstance(l, float) and isinstance(r, float):
            if op == TokenType.PLUS:
                return l + r
            else:
                return l - r
        if (isinstance(r, (float, XVar))) and op == TokenType.MINUS:
            return Triplet(left=l, op=op, right=-r)
        return Triplet(left=l, op=op, right=r)

    def visit_binary(self, node: BinOp) -> object:
        self.level += 1
        l = node.left.accept(self)
        r = node.right.accept(self)
        self.level -= 1
        if node.op.type in (TokenType.CIRCUMFLEX, TokenType.DOUBLESTAR):
            return self._handle_pow(l, r)
        if node.op.type in (TokenType.STAR,):
            return self._handle_mul(l, r)
        if node.op.type in (TokenType.PLUS, TokenType.MINUS):
            return self._handle_add_sub(l, r, node.op.type)
        return Triplet(
            left=l,
            op=node.op.type,
            right=r,
        )

    def visit_unary(self, node: UnOp) -> float | XVar:
        self.level += 1
        right = node.right.accept(self)
        self.level -= 1
        if isinstance(right, (float, XVar)):
            if node.op.type == TokenType.MINUS:
                return -right
            elif node.op.type == TokenType.PLUS:
                return right

        raise TypeError(f"Got invalid op type {node.op.type}")

    def visit_number(self, node: Number) -> float:
        return node.value

    def visit_variable(self, node: Variable) -> XVar:
        return XVar(degree=1)

    def visit_grouping(self, node: Grouping) -> object:
        return self.evaluate(node.expression)

    def evaluate(self, expr: Expr) -> object:
        self.level += 1
        e = expr.accept(self)
        self.level -= 1
        return e

    def exec(self, expr: Expr) -> object:
        self.level = 0
        if not isinstance(expr, BinOp) or expr.op.type != TokenType.EQUAL:
            raise RuntimeError("Missing equality")
        return expr.accept(self)


class Input:
    _scn: Scanner
    _prs: Parser
    _tks: list[Token]

    def __init__(self) -> None:
        pass

    def string(self, s: str):
        self._scn = Scanner(s)
        return self

    def get(self):
        self._scn = Scanner(input(">"))
        return self

    def parse(self):
        self._tks = self._scn.lex()
        self._prs = Parser(self._tks)
        return self._prs.parse()
