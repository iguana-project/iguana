import random
import string

# generate secret key
SECRET_KEY = ''.join([random.SystemRandom().choice(string.digits + string.ascii_uppercase
                      + string.ascii_lowercase + '!@#$%^&*(-_=+)')
                     for _ in range(50)])

print(SECRET_KEY, end="")
