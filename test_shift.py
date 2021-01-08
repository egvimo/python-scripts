import shift

def run_test(input, output):
    result = shift.shift(input)
    assert result == output

def test_shift():
    run_test('Hello World', 'Ifmmp Xpsme')
    run_test('xyz', 'yza')
    run_test('   ', '   ')
    run_test('012', '123')
    run_test('789', '890')
    run_test('+#-.', '+#-.')
    run_test('ab1 2+#', 'bc2 3+#')
