import numpy as np
from performance.caching import simple_cache
from utils import extract_rating_by_time, discretize, extract_sorted_rating_with_time, clean_folders, timestamp_to_date
import warnings
import os

from drawing import draw_rating_plot

RESULT_FOLDER = "rating_plots"

def _construct_linear_smoother(weights):
    def linear_smoother(X):
        S = []
        lx = len(X)
        lw = len(weights)
        for i, x in enumerate(X):
            s = 0
            for j, w in zip(range(i - lw//2, i + lw//2), weights):
                if j < 0:
                    s += X[0]*w
                elif j >= lx:
                    s += X[lx-1]*w
                else:
                    s += X[j]*w
            S.append(s)
        return np.asarray(S)
    return linear_smoother

def _construct_default_linear_smoother():
    return _construct_linear_smoother([0.05, 0.1, 0.2, 0.3, 0.2, 0.1, 0.05])

def _construct_strong_linear_smoother():
    W = np.exp(-np.square(np.arange(-6, 7))/16) # Gaussian smoother
    return _construct_linear_smoother(W/sum(W))


@simple_cache("tag_time_rating.pkl")
def _get_normalized_density(data, tag_groups, discretizing_divisor, begin_time, end_time):

    def data_producer():
        l = len(tag_groups)
        for i, tag_group in enumerate(tag_groups):
            if type(tag_group) is str:
                tag_group = {tag_group}
            print("{}/{} ({})".format(i+1, l, str(tag_group)))
            try:
                T, R = extract_rating_by_time(data, lambda v: any([tag in v["tags"] for tag in tag_group]))
                yield T, R, tag_group
            except RuntimeError as re:
                warnings.warn("No such tags: {}".format(str(tag_group)), RuntimeWarning)

    def frequency_sorter_function(X):
        return np.max(X) - np.min(X)

    tag_time_rating = []
    for T, R, tag_group in data_producer():
        T = discretize(T, discretizing_divisor=discretizing_divisor, begin_x=begin_time, end_x=end_time, normalize=True)
        swing = frequency_sorter_function(T)
        tag_time_rating.append([swing, tag_group, T])

    return sorted(tag_time_rating, key=lambda x: -x[0])


def analyze_density_by_tag_and_time(data, begin_time=None, end_time=None, tag_groups=None,
            discretizing_divisor=24*60*60, number_of_precise_ratings=26, number_of_peaks=8):

    print("Analyzing density by tag and time")

    clean_folders([RESULT_FOLDER])

    if tag_groups is None:
        tag_groups = [
            "ветераны", "великая отечественная война",
            "9 мая", "8 марта", "хэллоуин", "новый год", "диплом",
            {"рубль", "доллар"}, "трамп", "турция", "великобритания", "санкции", {"игил", "сирия"}, "беженцы",
            {"донецк", "днр"}, {"майдан", "евромайдан"}, "крым", "ато",
            "поезд", "долг", "почта", "трамвай", "детский сад", "общежитие",
            {"fallout", "fallout 4"}, "gta 5", "dark souls", {"ведьмак", "ведьмак 3"}, "overwatch",
            "мстители", "спойлер", "deadpool", "игра престолов", "star wars",
            "осень", "зима",
            "цыгане", "обида", "свадьба", "мошенники", "оскар",
            "лига детективов", "санкции", "собеседование", "несправедливость", "родственники", "торрент", "кризис",
            "леонардо ди каприо", "хоккей", "футбол", "покемоны", "хоббит"
        ]

    print("Computing normalized density")
    tag_time_rating = _get_normalized_density(data,
             tag_groups,
             discretizing_divisor=discretizing_divisor,
             begin_time=begin_time,
             end_time=end_time)

    groups_per_plot = {
        "seasonal" : {
            "group" : ["9 мая", "8 марта", "хэллоуин", "новый год", "диплом", "осень", "зима"],
            "smoother" : _construct_default_linear_smoother(),
            "draw_precise_plots" : False
        },
        "politics_1" : {
            "group" : [{"рубль", "доллар"}, "турция", "великобритания", "санкции", "трамп", {"игил", "сирия"}, "беженцы"],
            "smoother" : _construct_default_linear_smoother(),
            "draw_precise_plots" : False
        },
        "politics_2" : {
            "group" : [{"донецк", "днр"}, {"майдан", "евромайдан"}, "крым", "ато"],
            "smoother" : _construct_default_linear_smoother(),
            "draw_precise_plots" : False
        },
        "veterans" : {
            "group" : ["ветераны", "великая отечественная война"],
            "smoother" : _construct_default_linear_smoother(),
            "draw_precise_plots" : False
        },
        "oscar" : {
            "group" : ["оскар", "леонардо ди каприо"],
            "smoother" : _construct_default_linear_smoother(),
            "draw_precise_plots" : False
        },
        "hype_1" : {
            "group" : ["цыгане", "лига детективов", "собеседование", "несправедливость", "родственники", "торрент", "кризис"],
            "smoother" : _construct_default_linear_smoother(),
            "draw_precise_plots" : True
        },
        "hype_2" : {
            "group" : ["поезд", "долг", "почта", "трамвай", "детский сад", "общежитие"],
            "smoother" : _construct_strong_linear_smoother(),
            "draw_precise_plots" : True
        },
        "sports" : {
            "group" : ["хоккей", "футбол"],
            "smoother" : _construct_default_linear_smoother(),
            "draw_precise_plots" : True
        },
        "games" : {
            "group" : ["покемоны", {"fallout", "fallout 4"}, "gta 5", "dark souls", {"ведьмак", "ведьмак 3"}, "overwatch"],
            "smoother" : _construct_strong_linear_smoother(),
            "draw_precise_plots" : True
        },
        "universe" : {
            "group" : ["star wars", "хоббит", "мстители", "спойлер", "deadpool", "игра престолов"],
            "smoother" : _construct_strong_linear_smoother(),
            "draw_precise_plots" : True
        }
    }

    for key, config in groups_per_plot.items():

        print("Drawing {}".format(key))

        group, smoother, draw_precise_plots = config["group"], config["smoother"], config["draw_precise_plots"]
        plots, labels, captions_batches, vline_batches = [], [], [], []

        T = None
        for tag in group:
            try:
                record = next(record for record in tag_time_rating if (tag in record[1] or tag == record[1]))
                normalized_density = smoother(record[2])
                if T is None:
                    T = np.arange(len(normalized_density))*discretizing_divisor + begin_time

                if draw_precise_plots:
                    T2, R = extract_sorted_rating_with_time(data, lambda v: tag in v["tags"] or tag == record[1])
                    current_vlines = [
                        [
                            T2[i],
                            0,
                            "пост с рейтингом " + str(R[i]) + " (" + timestamp_to_date(T2[i]) + ")"
                        ]
                        for i in range(number_of_precise_ratings)]
                    current_vlines = sorted(current_vlines, key=lambda x: -x[0])
                    for i in range(number_of_precise_ratings):
                        current_vlines[i][1] = max(normalized_density)*(number_of_precise_ratings-i)/(number_of_precise_ratings+1)
                    vline_batches.append(current_vlines)

                    strong_maximums = []
                    for i in range(1, len(normalized_density)):
                        if normalized_density[i] > normalized_density[i-1] and normalized_density[i] > normalized_density[i+1]:
                            strong_maximums.append(normalized_density[i])
                    sorted_strong_maximums = sorted(strong_maximums, reverse=True)

                    peak_idxes = [np.where(normalized_density==d)[0][0] for d in sorted_strong_maximums[:number_of_peaks]]
                    captions_batches.append([
                        (
                            T[max_idx],
                            normalized_density[max_idx],
                            "пик " + " " + timestamp_to_date(T[max_idx])
                        )
                    for max_idx in peak_idxes])

                plots.append(normalized_density)
                if type(tag) is str:
                    labels.append(tag)
                else:
                    labels.append("+".join(tag))
            except StopIteration as si:
                warnings.warn("No such tag in tag_time_rating: {}".format(str(tag)), RuntimeWarning)
            except RuntimeError as re:
                warnings.warn("No such tag in data: {}".format(str(tag)), RuntimeWarning)

        if plots:
            name = os.path.join(RESULT_FOLDER, key + ".png")
            draw_rating_plot(T, plots, labels,
                             begin_time=begin_time, end_time=end_time,
                             path_to_save=name)
            name = os.path.join(RESULT_FOLDER, "lores_" + key + ".png")
            draw_rating_plot(T, plots, labels,
                             begin_time=begin_time, end_time=end_time,
                             path_to_save=name, figsize=(14, 8))
            if draw_precise_plots:
                for idx, (plot, label, vlines, captions) in enumerate(zip(plots, labels, vline_batches, captions_batches)):
                    print("Drawing {} precise: {}".format(key, label))
                    draw_rating_plot(T, [plot], [label],
                                     begin_time=begin_time, end_time=end_time,
                                     path_to_save=os.path.join(RESULT_FOLDER, key + "_precise_" + str(idx) + "_(" + label + ").png"),
                                     vlines=vlines, captions=captions, figsize=(60, 30))
        else:
            warnings.warn("No plots are drawn. Check 'groups_per_plot' - "
                          "are you sure they composed of same tags as 'tag_groups'", RuntimeWarning)
