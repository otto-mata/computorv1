class EqualityMember:
    exp: list[float]

    def __init__(self, *args: int) -> None:
        self.exp = []

    def push_factor(self, factor: float) -> None: ...

    @property
    def degree(self):
        return len(self.exp) - 1


class Equation:
    def __init__(self, *args: int) -> None:
        pass


class Parser:
    @staticmethod
    def new_equation_from_string(inp: str) -> Equation:
        first, second = [*map(lambda x: x.strip(), inp.split("="))]
        Parser.new_member_from_string(first)
        Parser.new_member_from_string(second)
        return Equation()

    @staticmethod
    def new_member_from_string(inp: str) -> EqualityMember:
        print(inp)
        return EqualityMember()


Parser.new_equation_from_string("5 * X^0 + 4 * X^1 - 9.3 * X^2 = 1 * X^0")
