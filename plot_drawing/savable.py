import functools
import warnings
import matplotlib.pyplot as plt

def savable(default_save=False, default_path_to_save=None):
    """
    Ensure 'savable' is the last decorator applied to plot
    :param default_save: If True saves plot by default. Otherwise 'should_save' should be explicitely saved to True
    :param default_path_to_save: Default path to save if no 'path_to_save' provided
    :return:
    """
    def savable_wraper(func):
        @functools.wraps(func)
        def saver(*args, **kwargs):
            ret = func(*args, **kwargs)
            if "should_save" in kwargs:
                should_save = kwargs["should_save"]
            else:
                should_save = default_save
            if "path_to_save" in kwargs:
                path_to_save = kwargs["path_to_save"]
            else:
                if should_save:
                    path_to_save = default_path_to_save
                    if path_to_save is None:
                        warnings.warn("Plot should be saved, but no path to save provided. Showing instead", RuntimeWarning)
                        should_save = False
            if should_save:
                plt.savefig(path_to_save)
            else:
                plt.show()
            plt.close('all')
            return ret
        return saver
    return savable_wraper
