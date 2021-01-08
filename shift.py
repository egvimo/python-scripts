#!/usr/bin/env python3

import argparse

letters = 'abcdefghijklmnopqrstuvwxyz'
digits = '0123456789'


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Shift characters by the given amount')
    parser.add_argument('-m', '--message', type=str,
                        help='message to be shifted')
    parser.add_argument('-s', '--shift-amount', default=1, type=int,
                        help='amount to shift the characters (default: 1)')

    args = parser.parse_args()

    if not args.message:
        args.message = input("Message: ")

    return args


def shift_letter(char):
    isUpper = char.isupper()
    current_position = letters.index(char.lower())
    result = letters[(current_position + args.shift_amount) % len(letters)]

    return result.upper() if isUpper else result


def shift_digit(char):
    current_position = digits.index(char)
    result = digits[(current_position + args.shift_amount) % len(digits)]

    return result


def shift(args):
    result = ''

    for char in args.message:
        if char.lower() in letters:
            result += shift_letter(char)
        elif char.lower() in digits:
            result += shift_digit(char)
        else:
            result += char

    return result


if __name__ == '__main__':
    args = parse_arguments()
    print(shift(args))
