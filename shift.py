#!/usr/bin/env python3

"""Shifts letters and digits by the given amount."""

import argparse

LETTERS = 'abcdefghijklmnopqrstuvwxyz'
DIGITS = '0123456789'


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Shift characters by the given amount')
    parser.add_argument('-m', '--message', type=str,
                        help='message to be shifted')
    parser.add_argument('-s', '--shift-amount', default=1, type=int,
                        help='amount to shift the characters (default: 1)')

    arguments = parser.parse_args()

    if not arguments.message:
        arguments.message = input("Message: ")

    return arguments


def shift_letter(char, shift_amount):
    """Shifts letters by the given amount."""
    current_position = LETTERS.index(char.lower())
    result = LETTERS[(current_position + shift_amount) % len(LETTERS)]

    return result.upper() if char.isupper() else result


def shift_digit(char, shift_amount):
    """Shifts digits by the given amount."""
    current_position = DIGITS.index(char)
    result = DIGITS[(current_position + shift_amount) % len(DIGITS)]

    return result


def shift(message, shift_amount=1):
    """Shifts letters and digits by the given amount, ignoring all other characters."""
    result = ''

    for char in message:
        if char.lower() in LETTERS:
            result += shift_letter(char, shift_amount)
        elif char.lower() in DIGITS:
            result += shift_digit(char, shift_amount)
        else:
            result += char

    return result


if __name__ == '__main__':
    args = parse_arguments()
    print(shift(args.message))
