import secrets

# Generate a secure random secret key
secret_key = secrets.token_hex(24)
print(secret_key)
