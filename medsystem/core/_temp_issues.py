# Temporary file with intentional issues for SonarCloud demonstration

import logging

# 1) Mutable default argument (bug)


def collect_items(item, items=[]):
    items.append(item)
    return items


# 2) Bare except (code smell)


def risky_divide(a, b):
    try:
        return a / b
    except:
        return None


# 3) Unused variable (code smell)


def do_nothing():
    x = 42
    return True


# 4) Duplicate code blocks (duplication)


def process_a(data):
    result = []
    for d in data:
        if d % 2 == 0:
            result.append(d * 2)
        else:
            result.append(d + 1)
    return result


def process_b(data):
    result = []
    for d in data:
        if d % 2 == 0:
            result.append(d * 2)
        else:
            result.append(d + 1)
    return result


# 5) Long function with many branches (complexity)


def complex_function(n):
    if n == 0:
        return 0
    elif n == 1:
        return 1
    elif n == 2:
        return 2
    elif n == 3:
        return 3
    elif n == 4:
        return 4
    elif n == 5:
        return 5
    elif n == 6:
        return 6
    elif n == 7:
        return 7
    elif n == 8:
        return 8
    elif n == 9:
        return 9
    else:
        return -1
