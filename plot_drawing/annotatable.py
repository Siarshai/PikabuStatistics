import functools
import warnings
import matplotlib.pyplot as plt

def annotatable(func):
    @functools.wraps(func)
    def annotater(*args, **kwargs):
        ret = func(*args, **kwargs)
        ax = plt.gca()
        if ax is None:
            warnings.warn("Can not annotate plot: no gca(). Are you sure you apply decorators in right order?")
        if "vlines" in kwargs:
            for x, y, text in kwargs["vlines"]:
                ax.axvline(x, color='k', linestyle='--')
                ax.annotate(text, xy=(x, y))
        if "hlines" in kwargs:
            for x, y, text in kwargs["hlines"]:
                ax.axhline(y, color='k', linestyle='--')
                ax.annotate(text, xy=(x, y))
        if "captions" in kwargs:
            for x, y, text in kwargs["captions"]:
                ax.annotate(text, xy=(x, y))
        if "scatter" in kwargs:
            x, y = zip(*kwargs["scatter"])
            ax.scatter(x, y, color="r")
        return ret
    return annotater
