_print = print


def print(*what):
    _print(*what, end="\n\n")
