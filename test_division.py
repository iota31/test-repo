from buggy_code import divide_numbers

def test_divide_numbers():
    # Test division by non-zero number
    results = divide_numbers(10, 2)
    print(f'Result of 10 / 2: {results}')
    # Test division by zero
    results = divide_numbers(10, 0)
    print(f'Result of 10 / 0: {results}')

test_divide_numbers()