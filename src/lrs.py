# Adapted from https://eprint.iacr.org/2004/027.pdf
# See above for more details.

from util import Constants, powm, randkey
from hashlib import sha1


def sign(msg, x_i, idx, L, g=Constants.G, p=Constants.P, q=Constants.Q):
	"""Signs a message using a linkable ring signature.

	msg: The message to be signed
	x_i: The private key of the signer
	idx: The index of the public key in L
	L: List of public keys

	Returns the signature.
	"""
	n = len(L)
	c = [0 for _ in range(n)]
	s = [0 for _ in range(n)]

	# step 1
	h = H2(L, g, p, q)
	t = powm(h, x_i, p)

	# step 2
	u = randkey(0, q - 1)
	c[(idx + 1) % n] = H1([L, t, msg, powm(g, u, p), powm(h, u, p)])

	# step 3
	i = (idx + 1) % n
	while i != idx:
		s[i] = randkey(0, q - 1)
		z_1 = (powm(g, s[i], p) * powm(L[i], c[i], p)) % p
		z_2 = (powm(h, s[i], p) * powm(t, c[i], p)) % p
		c[(i + 1) % n] = H1([L, t, msg, z_1, z_2])
		i = (i + 1) % n

	# step 4
	s[idx] = (u - ((x_i * c[idx]) % q)) % q

	return (c[0], s, t)


def verify(msg, L, c_0, s, t, g=Constants.G, p=Constants.P, q=Constants.Q):
	"""Verifies a message signed with a linkable ring signature.

	msg: The message to be signed
	L: List of public keys
	c_0, s, t: The values returned by sign()

	Returns whether the signature is valid.
	"""
	n = len(L)
	c = [0 for _ in range(n)]
	c[0] = c_0

	h = H2(L, g, p, q)

	for i in range(n):
		z_1 = (powm(g, s[i], p) * powm(L[i], c[i], p)) % p
		z_2 = (powm(h, s[i], p) * powm(t, c[i], p)) % p
		c[(i + 1) % n] = H1([L, t, msg, z_1, z_2])

	return c_0 == c[0]


def H1(msg):
	"""Hash function 1."""
	msg = str(msg).encode(Constants.ENCODING)
	return int(sha1(msg).hexdigest(), 16)


def H2(msg, g, p, q):
	"""Hash function 2."""
	val = H1(msg) % q
	return powm(g, val, p)
