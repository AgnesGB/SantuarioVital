# Fixed version of the temporary issues
import logging

# 1) Mutable default argument fixed


def collect_items(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items


# 2) Handle specific exception and log


def risky_divide(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        logging.exception("Division by zero attempted")
        return None


# 3) Removed unused variable


def do_nothing():
    return True


# 4) Extracted helper to remove duplication


def _process_generic(data):
    result = []
    for d in data:
        if d % 2 == 0:
            result.append(d * 2)
        else:
            result.append(d + 1)
    return result


def process_a(data):
    return _process_generic(data)


def process_b(data):
    return _process_generic(data)


# 5) Simplified complex function


def complex_function(n):
    if 0 <= n <= 9:
        return n
    return -1
