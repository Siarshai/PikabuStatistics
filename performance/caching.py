import functools
import os.path
import pickle
import warnings

def simple_cache(cache_file):
    def simple_cache_wrapper(func):

        @functools.wraps(func)
        def cacher(*args, **kwargs):
            read_well = False
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, "rb") as handle:
                        retval = pickle.load(handle)
                        read_well = True
                except IOError as e:
                    warnings.warn("Simple cache file {} exists but read failed".format(cache_file), e)

            if not read_well:
                retval = func(*args, **kwargs)
                try:
                    with open(cache_file, "wb") as handle:
                        pickle.dump(retval, handle, protocol=pickle.HIGHEST_PROTOCOL)
                except IOError as e:
                    warnings.warn("Could not write simple cache file {}".format(cache_file), e)
            return retval

        cacher.cache_file = cache_file

        def clean_cache():
            try:
                if os.path.exists(cache_file):
                    os.remove(cache_file)
            except OSError as ose:
                warnings.warn("Tried to remove cache file {} but failed: {}".format(cache_file, str(ose)))

        cacher.clean_cache = clean_cache

        return cacher
    return simple_cache_wrapper


def save_code_based_cache(cache_file):
    def save_code_cache_wrapper(func):

        @functools.wraps(func)
        def cacher(*args, **kwargs):
            save_code = kwargs["save_code"] if "save_code" in kwargs else 0
            read_well = False
            cache_dict = {}
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, "rb") as handle:
                        cache_dict = pickle.load(handle)
                        if save_code in cache_dict:
                            retval = cache_dict[save_code]
                            read_well = True
                except IOError as e:
                    warnings.warn("Save code based cache file {} exists but read failed".format(cache_file), e)

            if not read_well:
                retval = func(*args, **kwargs)
                try:
                    with open(cache_file, "wb") as handle:
                        cache_dict[save_code] = retval
                        pickle.dump(cache_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
                except IOError as e:
                    warnings.warn("Could not write save code based cache file {}".format(cache_file), e)
            return retval

        cacher.cache_file = cache_file

        def clean_cache():
            try:
                if os.path.exists(cache_file):
                    os.remove(cache_file)
            except OSError as ose:
                warnings.warn("Tried to remove cache file {} but failed: {}".format(cache_file, str(ose)))

        cacher.clean_cache = clean_cache

        return cacher
    return save_code_cache_wrapper
