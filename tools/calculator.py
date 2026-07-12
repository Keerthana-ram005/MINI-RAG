import re


def calculator(query: str):
    """
    Evaluates simple mathematical expressions from a text query.
    Examples:
        '2 + 3'
        'calculate (10 + 5) * 2'
        '100 / 4'
    """

    try:
        # Keep only numbers, operators, parentheses, and spaces
        expression = re.sub(r"[^0-9+\-*/(). ]", "", query)

        if not expression.strip():
            return "No valid mathematical expression found."

        result = eval(expression)

        return f"The answer is {result}"

    except Exception:
        return "Sorry, I couldn't calculate that."