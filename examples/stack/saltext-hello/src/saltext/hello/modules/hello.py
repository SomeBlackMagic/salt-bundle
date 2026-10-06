"""Salt execution module providing hello.greet function."""


__virtualname__ = "hello"


def __virtual__():
    return __virtualname__


def greet(name="World"):
    """
    Return a greeting message.

    CLI Example:

    .. code-block:: bash

        salt '*' hello.greet
        salt '*' hello.greet name="Salt"
    """
    return f"Hello, {name}!"
