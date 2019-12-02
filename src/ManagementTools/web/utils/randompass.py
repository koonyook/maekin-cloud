import random
import string


def GenPasswd2(length=8, chars=string.letters + string.digits):
    return ''.join([chars[random.randint(0,61)] for i in range(length)])
