import bcrypt


def hash_password(password: str) -> str:
	salt = bcrypt.gensalt()
	return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(suggested_password: str, hashed_password: str) -> bool:
	return bcrypt.checlpw(
			suggested_password.encode('utf-8'),
			hash_password.encode('utf-8')
		)
