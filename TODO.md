# To do

## Main points

[] Expression parser
[] Equation reducer
[] Discriminants calculator

## Specifics

### Expression parser

- Store power of X factors in an array
  i.e.: "5 * X^0 + 4 * X^1 - 9.3 * X^2 = 1 * X^0" => [5, 4, -9.3] = [1]
        "8 * X^0 - 6 * X^1 + 0 * X^2 - 5.6 * X^3 = 3 * X^0" => [8, -6, 0, -5.6] = [3]
- Get max degree from the biggest power (degree = index i in the powers' array)

### Equation reducer

- Reorganize members to the left, aiming for equality to 0
  i.e.: [5, 4, -9.3] = [1] => [4, 4, -9.3] = 0, substracting the 1×X⁰
        [8, -6, 0, -5.6] = [3] => [5, -6, 0, -5.6] = 0, substracting the 3×X⁰

### Discriminants calculator
