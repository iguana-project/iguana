#!/bin/python

import random

# generate secret key
SECRET_KEY = ''.join([random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)')
                      for _ in range(50)])

print(SECRET_KEY, end="")
