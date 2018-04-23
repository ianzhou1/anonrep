# https://eprint.iacr.org/2004/027.pdf
# See above for more details.

from util import Constants, powm, randkey
from hashlib import sha1

# sign a message using a linkable ring signature
def sign(msg, x_i, idx, L, g=Constants.G, p=Constants.P, q=Constants.Q):
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

# verify a message and linkable ring signature
def verify(msg, L, c_0, s, t, g=Constants.G, p=Constants.P, q=Constants.Q):
	n = len(L)
	c = [0 for _ in range(n)]
	c[0] = c_0

	h = H2(L, g, p, q)

	for i in range(n):
		z_1 = (powm(g, s[i], p) * powm(L[i], c[i], p)) % p
		z_2 = (powm(h, s[i], p) * powm(t, c[i], p)) % p
		c[(i + 1) % n] = H1([L, t, msg, z_1, z_2])

	return c_0 == c[0]

# hash function 1
def H1(msg):
	msg = concat(msg).encode(Constants.ENCODING)
	return int(sha1(msg).hexdigest(), 16)

# hash function 2
def H2(msg, g, p, q):
	val = H1(msg) % q
	return powm(g, val, p)

# convert args into string
def concat(args):
	ret = []
	for a in args:
		if isinstance(a, list):
			ret.append(concat(a))
		else:
			ret.append(str(a))

	return ''.join(ret)
