# Copyright (c) 2018-2019 hippo91 <guillaume.peillex@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER

# TODO(hippo91) : correct the functions return types
"""Astroid hooks for numpy.random.mtrand module."""

import astroid


def numpy_random_mtrand_transform():
    return astroid.parse(
        """
    def beta(a, b, size=None): return uninferable
    def binomial(n, p, size=None): return uninferable
    def bytes(length): return uninferable
    def chisquare(df, size=None): return uninferable
    def choice(a, size=None, replace=True, p=None): return uninferable
    def dirichlet(alpha, size=None): return uninferable
    def exponential(scale=1.0, size=None): return uninferable
    def f(dfnum, dfden, size=None): return uninferable
    def gamma(shape, scale=1.0, size=None): return uninferable
    def geometric(p, size=None): return uninferable
    def get_state(): return uninferable
    def gumbel(loc=0.0, scale=1.0, size=None): return uninferable
    def hypergeometric(ngood, nbad, nsample, size=None): return uninferable
    def laplace(loc=0.0, scale=1.0, size=None): return uninferable
    def logistic(loc=0.0, scale=1.0, size=None): return uninferable
    def lognormal(mean=0.0, sigma=1.0, size=None): return uninferable
    def logseries(p, size=None): return uninferable
    def multinomial(n, pvals, size=None): return uninferable
    def multivariate_normal(mean, cov, size=None): return uninferable
    def negative_binomial(n, p, size=None): return uninferable
    def noncentral_chisquare(df, nonc, size=None): return uninferable
    def noncentral_f(dfnum, dfden, nonc, size=None): return uninferable
    def normal(loc=0.0, scale=1.0, size=None): return uninferable
    def pareto(a, size=None): return uninferable
    def permutation(x): return uninferable
    def poisson(lam=1.0, size=None): return uninferable
    def power(a, size=None): return uninferable
    def rand(*args): return uninferable
    def randint(low, high=None, size=None, dtype='l'): 
        import numpy
        return numpy.ndarray((1,1))
    def randn(*args): return uninferable
    def random_integers(low, high=None, size=None): return uninferable
    def random_sample(size=None): return uninferable
    def rayleigh(scale=1.0, size=None): return uninferable
    def seed(seed=None): return uninferable
    def set_state(state): return uninferable
    def shuffle(x): return uninferable
    def standard_cauchy(size=None): return uninferable
    def standard_exponential(size=None): return uninferable
    def standard_gamma(shape, size=None): return uninferable
    def standard_normal(size=None): return uninferable
    def standard_t(df, size=None): return uninferable
    def triangular(left, mode, right, size=None): return uninferable
    def uniform(low=0.0, high=1.0, size=None): return uninferable
    def vonmises(mu, kappa, size=None): return uninferable
    def wald(mean, scale, size=None): return uninferable
    def weibull(a, size=None): return uninferable
    def zipf(a, size=None): return uninferable
    """
    )


astroid.register_module_extender(
    astroid.MANAGER, "numpy.random.mtrand", numpy_random_mtrand_transform
)
