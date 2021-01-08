import shift
import pytest


@pytest.mark.parametrize(('message', 'result'), [
    ('Test', 'Uftu'),
    ('123', '234'),
    ('Test 123', 'Uftu 234'),
    ('xyz', 'yza'),
    ('+#.', '+#.'),
    ('789', '890'),
    ('ABCxyz-012789', 'BCDyza-123890')
])
def test_shift(message, result):
    assert shift.shift(message) == result
