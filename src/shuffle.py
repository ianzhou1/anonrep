# http://web.cs.elte.hu/~rfid/p116-neff.pdf
# See above for more details.

import random
from util import Constants, send, recv, randkey, powm, modinv, divide


def generate_permutation(n):
	"""Returns a permutation of a list containing the integers from 0 to n - 1."""
	pi = [_ for _ in range(n)]
	random.shuffle(pi)
	return pi


def shuffle(elts, pi):
	"""Shuffles elts according to the permutation list pi."""
	return [elts[pi[i]] for i in range(len(elts))]


def _prove_simple(sock, gamma, r, s,
		g=Constants.G, p=Constants.P, q=Constants.Q):
	assert(len(r) == len(s))
	n = len(r)

	# step 1
	t = recv(sock)

	# step 2
	r_hat = [(r[i] - t) % q for i in range(n)]
	s_hat = [(s[i] - gamma * t) % q for i in range(n)]
	theta = [0] + [randkey(0, q - 1) for _ in range(2 * n - 1)]
	Theta = []
	for i in range(2 * n):
		if i < n:
			exp = (theta[i] * r_hat[i]) % q
			exp -= (theta[i + 1] * s_hat[i]) % q
			exp %= q
			Theta.append(powm(g, exp, p))
		else:
			exp = (theta[i] * gamma) % q
			exp -= theta[(i + 1) % (2 * n)]
			exp %= q
			Theta.append(powm(g, exp, p))
	send(sock, Theta)

	# step 3
	c = recv(sock)

	# step 4
	alpha = [c]
	tmp = c
	for i in range(2 * n - 1):
		if i < n:
			tmp = (tmp * divide(r_hat[i], s_hat[i], q)) % q
			alpha.append((tmp + theta[i + 1]) % q)
		elif i == n:
			inv = modinv(gamma, q)
			tmp = (c * powm(inv, (2 * n - 1) - i, q)) % q
			alpha.append((tmp + theta[i + 1]) % q)
		else:
			tmp = (tmp * gamma) % q
			alpha.append((tmp + theta[i + 1]) % q)
	send(sock, alpha)


def _verify_simple(sock, Gamma, R, S,
		g=Constants.G, p=Constants.P, q=Constants.Q):
	assert(len(R) == len(S))
	n = len(R)

	# step 1
	t = randkey(0, q - 1)
	send(sock, t)

	# step 2
	Theta = recv(sock)

	# step 3
	c = randkey(0, q - 1)
	send(sock, c)

	# step 4
	alpha = recv(sock)

	# step 5
	U = powm(g, -t % q, p)
	W = powm(Gamma, -t % q, p)
	R_hat = [(R[i] * U) % p for i in range(n)]
	S_hat = [(S[i] * W) % p for i in range(n)]

	ret = True
	for i in range(2 * n):
		if i < n:
			ver = powm(R_hat[i], alpha[i], p) * powm(S_hat[i], -alpha[i + 1] % q, p)
			ver %= p
			ret = ret and (Theta[i] == ver)
		else:
			ver = powm(Gamma, alpha[i], p) * powm(g, -alpha[(i + 1) % (2 * n)] % q, p)
			ver %= p
			ret = ret and (Theta[i] == ver)

	return ret


"""
def prove_general(sock, nym_pre, nym_post, gamma, u, v,
		g=Constants.G, p=Constants.P, q=Constants.Q):
	assert(len(u) == len(v))
	n = len(u)

	U = [powm(g, u[i], p) for i in range(n)]
	V = [powm(g, v[i], p) for i in range(n)]

	# nym proof
	a = [randkey(0, q - 1) for _ in range(n)]
	b = [randkey(0, q - 1) for _ in range(n - 1)]
	b.append(sum([(b[i] * v[i]) % q for i in range(n - 1)]) % q)
	b[-1] = (b[-1] - gamma * sum([(a[i] * u[i]) % q for i in range(n)]) % q) % q
	b[-1] = (b[-1] * modinv(v[-1], q)) % q
	A = [powm(g, a[i], p) for i in range(n)]
	B = [powm(g, b[i], p) for i in range(n)]

	lam = randkey(0, q - 1)

	s = [(a[i] + lam * u[i]) % q for i in range(n)]
	r = [(b[i] + lam * v[i]) % q for i in range(n)]

	P = 1
	Q = 1
	for i in range(n):
		P = (P * powm(nym_pre[i], r[i], p)) % p
		Q = (Q * powm(nym_post[i], s[i], p)) % p

	# print(P, Q, divide(P, Q, p), divide(Q, P, p))

	for i in range(n - 1):
		assert(powm(g, s[i], p) == (A[i] * powm(U[i], lam, p)) % p)
		assert(powm(g, r[i], p) == (B[i] * powm(V[i], lam, p)) % p)
"""


def prove(sock, elts_pre, elts_post, pi, beta, g_, h_,
		g=Constants.G, p=Constants.P, q=Constants.Q):
	"""Generate a zero-knowledge proof for the verifiable shuffle.

	sock: Socket to send messages through
	elts_pre: Elements before cryptographic operation
	elts_post: Elements after cryptographic operation
	pi: Permutation list
	beta, g_, h_: Verifiable shuffle parameters
	"""
	nym_pre = elts_pre[0]
	nym_post = elts_post[0]
	XY_pre = elts_pre[1]
	XY_post = elts_post[1]

	assert(len(nym_pre) == len(nym_post))
	assert(len(XY_pre) == len(XY_post))
	assert(len(nym_pre) == len(XY_pre))
	n = len(nym_pre)
	pi_inv = [_ for _ in range(n)]
	for i in range(n):
		pi_inv[pi[i]] = i

	# step 1
	a = [randkey(0, q - 1) for _ in range(n)]
	u = [randkey(0, q - 1) for _ in range(n)]
	w = [randkey(0, q - 1) for _ in range(n)]
	tau_0 = randkey(0, q - 1)
	gamma = randkey(1, q - 1)

	Gamma = powm(g, gamma, p)
	A = [powm(g, a[i], p) for i in range(n)]
	C = [powm(A[pi[i]], gamma, p) for i in range(n)]
	U = [powm(g, u[i], p) for i in range(n)]
	W = [powm(g, gamma * w[i], p) for i in range(n)]
	Lambda_1 = powm(g_, tau_0 + sum([(w[i] * beta) % q for i in range(n)]), p)
	Lambda_2 = powm(h_, tau_0 + sum([(w[i] * beta) % q for i in range(n)]), p)
	for i in range(n):
		X_i, Y_i = XY_pre[i]
		Lambda_1 = (Lambda_1 * powm(X_i, (w[pi_inv[i]] - u[i]) % q, p)) % p
		Lambda_2 = (Lambda_2 * powm(Y_i, (w[pi_inv[i]] - u[i]) % q, p)) % p
	send(sock, [A, C, U, W, Gamma, Lambda_1, Lambda_2])

	# step 2
	rho = recv(sock)

	# step 3
	b = [(rho[i] - u[i]) % q for i in range(n)]
	d = [(gamma * b[pi[i]]) % q for i in range(n)]
	D = [powm(g, d[i], p) for i in range(n)]
	send(sock, D)

	# step 4
	lam = recv(sock)

	# step 5
	r = [(a[i] + lam * b[i]) % q for i in range(n)]
	s = [(gamma * r[pi[i]]) % q for i in range(n)]
	sigma = [(w[i] + b[pi[i]]) % q for i in range(n)]
	tau = (-tau_0 + sum([(b[i] * beta) % q for i in range(n)])) % q
	send(sock, [tau, sigma])

	# step 6
	_prove_simple(sock, gamma, r, s, g, p, q)

	# nym proof
	# prove_general(sock, nym_pre, nym_post, gamma, r, s, g, p, q)


def verify(sock, elts_pre, elts_post, g_, h_,
		g=Constants.G, p=Constants.P, q=Constants.Q):
	"""Verify a zero-knowledge proof for the verifiable shuffle.

	sock: Socket to send messages through
	elts_pre: Elements before cryptographic operation
	elts_post: Elements after cryptographic operation
	g_, h_: Verifiable shuffle parameters
	"""
	nym_pre = elts_pre[0]
	nym_post = elts_post[0]
	XY_pre = elts_pre[1]
	XY_post = elts_post[1]

	assert(len(nym_pre) == len(nym_post))
	assert(len(XY_pre) == len(XY_post))
	assert(len(nym_pre) == len(XY_pre))
	n = len(nym_pre)

	# step 1
	A, C, U, W, Gamma, Lambda_1, Lambda_2 = recv(sock)

	# step 2
	rho = [randkey(0, q - 1) for _ in range(n)]
	B = [divide(powm(g, rho[i], p), U[i], p) for i in range(n)]
	send(sock, rho)

	# step 3
	D = recv(sock)

	# step 4
	lam = randkey(0, q - 1)
	send(sock, lam)

	# step 5
	tau, sigma = recv(sock)

	# step 6
	R = [(A[i] * powm(B[i], lam, p)) % p for i in range(n)]
	S = [(C[i] * powm(D[i], lam, p)) % p for i in range(n)]
	ret = _verify_simple(sock, Gamma, R, S, g, p, q)

	# step 7
	Phi_1 = 1
	Phi_2 = 1
	for i in range(n):
		X_i, Y_i = XY_pre[i]
		X_ibar, Y_ibar = XY_post[i]
		Phi_1 = (Phi_1 * powm(X_ibar, sigma[i], p) * powm(X_i, -rho[i] % q, p)) % p
		Phi_2 = (Phi_2 * powm(Y_ibar, sigma[i], p) * powm(Y_i, -rho[i] % q, p)) % p

	for i in range(n):
		ret = ret and (powm(Gamma, sigma[i], p) == (W[i] * D[i]) % p)

	ret = ret and (Phi_1 == (Lambda_1 * powm(g_, tau, p)) % p)
	ret = ret and (Phi_2 == (Lambda_2 * powm(h_, tau, p)) % p)

	return ret
