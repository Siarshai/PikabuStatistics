import datetime
import shutil
import os
import warnings

import numpy as np
from performance.caching import save_code_based_cache


def clean_folders(folders):
    for folder in folders:
        if os.path.exists(folder):
            for file in os.listdir(folder):
                file_path = os.path.join(folder, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path) #just in case
                except Exception as e:
                    warnings.warn(e)
        else:
            os.mkdir(folder)


def timestamp_to_date(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).strftime('%d-%m-%Y')


def discretize(X, Y=None, bins=None, discretizing_divisor=None, begin_x=None, end_x=None, normalize=True):
    if begin_x is None:
        begin_x = np.min(X)
    if end_x is None:
        end_x = np.max(X)
    if bins is not None:
        discretizing_divisor = float(end_x-begin_x)//bins + 1
    elif discretizing_divisor is not None:
        bins = float(end_x-begin_x)//discretizing_divisor + 1
    else:
        raise RuntimeError("Bins or discretizing divisor should be provided")

    X_discretized = np.zeros(bins)
    if Y is None:
        for x in X:
            bin_n = (x - begin_x) // discretizing_divisor
            if bin_n < 0: bin_n = 0
            if bin_n >= bins: bin_n = bins - 1
            X_discretized[bin_n] += 1
        if normalize: X_discretized /= len(X)
        return X_discretized
    else:
        Y_discretized = np.zeros(bins)
        for x, y in zip(X, Y):
            bin_n = (x - begin_x) // discretizing_divisor
            if bin_n < 0: bin_n = 0
            if bin_n >= bins: bin_n = bins - 1
            X_discretized[bin_n] += 1
            Y_discretized[bin_n] += y
        for i in range(len(Y_discretized)):
            if X_discretized[i] > 0:
                Y_discretized[i] /= X_discretized[i]
        if normalize: X_discretized /= len(X)
        return X_discretized, Y_discretized


def extract_rating_by_time(raw_data, filter_function):
    TR = [(v["timestamp"], v["rating"]) for v in raw_data.values() if filter_function(v)]
    if not TR:
        raise RuntimeError("Nothing matches filter function")
    T, R = zip(*sorted(TR, key=lambda x: x[0]))
    return np.asarray(T), np.asarray(R)


def extract_sorted_rating_with_time(raw_data, filter_function):
    TR = [(v["timestamp"], v["rating"]) for v in raw_data.values() if filter_function(v)]
    if not TR:
        raise RuntimeError("Nothing matches filter function")
    T, R = zip(*sorted(TR, key=lambda x: -x[1]))
    return np.asarray(T), np.asarray(R)


@save_code_based_cache("tags_filtered.pkl")
def filter_tags_by_occurency_number(data, tag_occurencies_filter, **kwargs):
    all_tags = dict()
    for post in data.values():
        for tag in post["tags"]:
            if tag in all_tags:
                all_tags[tag] += 1
            else:
                all_tags[tag] = 1
    return sorted([k for k, v in all_tags.items() if tag_occurencies_filter(v)])