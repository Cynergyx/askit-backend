import random
import string

def generate_complex_key(length=256):
    if length < 4:
        raise ValueError("Key length must be at least 4 to include all character sets.")

    # Character sets
    upper = string.ascii_uppercase
    lower = string.ascii_lowercase
    digits = string.digits
    # Exclude single and double quotes from punctuation
    symbols = ''.join(c for c in string.punctuation if c not in {'"', "'"})

    # Ensure at least one character from each set is included
    key = [
        random.choice(upper),
        random.choice(lower),
        random.choice(digits),
        random.choice(symbols)
    ]

    # Fill the rest of the key with random characters
    all_chars = upper + lower + digits + symbols
    key += random.choices(all_chars, k=length - 4)

    # Shuffle the key
    random.shuffle(key)

    return ''.join(key)

# Generate the key
complex_key = generate_complex_key()
print(complex_key)
