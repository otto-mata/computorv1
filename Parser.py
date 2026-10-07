from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from token import (
    CIRCUMFLEX,
    DOUBLESTAR,
    ENCODING,
    ENDMARKER,
    EQUAL,
    LPAR,
    MINUS,
    NAME,
    NEWLINE,
    NUMBER,
    PLUS,
    RPAR,
    SLASH,
    STAR,
)
from tokenize import TokenInfo
from typing import Generic, TypeVar

R = TypeVar("R")


class TokenType(Enum):
    MINUS = MINUS
    PLUS = PLUS
    SLASH = SLASH
    STAR = STAR
    EQUAL = EQUAL
    NUMBER = NUMBER
    NAME = NAME
    LPAR = LPAR
    RPAR = RPAR
    DOUBLESTAR = DOUBLESTAR
    CIRCUMFLEX = CIRCUMFLEX
    ENDMARKER = ENDMARKER
    ENCODING = ENCODING
    NEWLINE = NEWLINE


@dataclass
class Token:
    type: TokenType
    lexeme: str
    literal: float | None

    @staticmethod
    def from_token_info(ti: TokenInfo) -> Token:
        return Token(
            type=TokenType(ti.exact_type),
            lexeme=ti.string,
            literal=float(ti.string) if ti.type == NUMBER else None,
        )


class ExprVisitor(ABC, Generic[R]):
    @abstractmethod
    def visit_number(self, node: Number) -> R: ...
    @abstractmethod
    def visit_binary(self, node: BinOp) -> R: ...
    @abstractmethod
    def visit_grouping(self, node: Grouping) -> R: ...
    @abstractmethod
    def visit_unary(self, node: UnOp) -> R: ...
    @abstractmethod
    def visit_variable(self, node: Variable) -> R: ...


class Expr(ABC):
    @abstractmethod
    def accept(self, visitor: ExprVisitor[R]) -> R: ...


@dataclass(frozen=True)
class Number(Expr):
    value: float

    def accept(self, visitor: ExprVisitor[R]) -> R:
        return visitor.visit_number(self)


@dataclass(frozen=True)
class BinOp(Expr):
    left: Expr
    op: Token
    right: Expr

    def accept(self, visitor: ExprVisitor[R]) -> R:
        return visitor.visit_binary(self)


@dataclass(frozen=True)
class UnOp(Expr):
    op: Token
    right: Expr

    def accept(self, visitor: ExprVisitor[R]) -> R:
        return visitor.visit_unary(self)


@dataclass(frozen=True)
class Grouping(Expr):
    expression: Expr

    def accept(self, visitor: ExprVisitor[R]) -> R:
        return visitor.visit_grouping(self)


@dataclass(frozen=True)
class Variable(Expr):
    name: Token

    def accept(self, visitor: ExprVisitor[R]) -> R:
        return visitor.visit_variable(self)


class Parser:
    tokens: list[Token]
    current: int

    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.current = 0

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _is_at_end(self):
        return self._peek().type == TokenType.ENDMARKER

    def _check(self, type: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == type

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _match(self, *types: TokenType) -> bool:
        for type in types:
            if self._check(type):
                self._advance()
                return True
        return False

    def _expression(self) -> Expr:
        return self._equality()

    def _equality(self) -> Expr:
        expr = self._term()
        while self._match(TokenType.EQUAL):
            expr = BinOp(
                left=expr,
                op=self._previous(),
                right=self._term(),
            )
        return expr

    def _term(self) -> Expr:
        expr = self._factor()
        while self._match(
            TokenType.MINUS,
            TokenType.PLUS,
        ):
            expr = BinOp(
                left=expr,
                op=self._previous(),
                right=self._factor(),
            )
        return expr

    def _factor(self) -> Expr:
        expr = self._unary()
        while self._match(
            TokenType.SLASH,
            TokenType.STAR,
        ):
            expr = BinOp(
                left=expr,
                op=self._previous(),
                right=self._unary(),
            )
        return expr

    def _unary(self) -> Expr:
        if self._match(
            TokenType.MINUS,
            TokenType.PLUS,
        ):
            return UnOp(
                op=self._previous(),
                right=self._unary(),
            )
        return self._power()

    def _power(self) -> Expr:
        expr = self._primary()
        if self._match(
            TokenType.CIRCUMFLEX,
            TokenType.DOUBLESTAR,
        ):
            expr = BinOp(
                left=expr,
                op=self._previous(),
                right=self._unary(),
            )
        return expr

    def _primary(self) -> Expr:
        if self._match(TokenType.NUMBER):
            lit = self._previous().literal
            assert lit is not None, (
                "literal should not be None when matching a number"
            )
            return Number(lit)
        if self._match(TokenType.NAME):
            return Variable(self._previous())
        if self._match(TokenType.LPAR):
            expr = self._expression()
            self._consume(TokenType.RPAR, "missing `)`")
            return Grouping(expression=expr)
        raise RuntimeError(self._peek())

    def _consume(self, type: TokenType, msg: str) -> Token:
        if self._check(type):
            return self._advance()
        raise RuntimeError(msg, self._peek())

    def parse(self) -> Expr:
        return self._expression()
