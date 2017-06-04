from itertools import product
import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rc, pyplot, pyplot, pyplot, pyplot, pyplot, pyplot
from plot_drawing.annotatable import annotatable
from plot_drawing.savable import savable
from behaviour.type_enfocement import enforce_kwargs

font = {'family': 'Verdana',
        'weight': 'normal'}
rc('font', **font)


def _generate_time_labels(begin_datetime, end_datetime):

    holidays_list = [
        (1, 1),
        (1, 3),
        (1, 4),
        (9, 5),
        (12, 6),
        (1, 9),
        (4, 11)
    ]

    T = []
    T_labels = []

    idx = 0
    if begin_datetime.day > holidays_list[-1][0] and begin_datetime.month > holidays_list[-1][1]:
        year = begin_datetime.year + 1
    else:
        for i, dm in enumerate(holidays_list):
            if dm[1] > begin_datetime.month or (dm[1] == begin_datetime.month and dm[0] >= begin_datetime.day):
                idx = i
                break
        year = begin_datetime.year

    it_datetime = datetime.datetime(year=year, month=holidays_list[idx][1], day=holidays_list[idx][0])
    while it_datetime < end_datetime:
        T.append(it_datetime.timestamp())
        T_labels.append("{}-{}-{}".format(it_datetime.day, it_datetime.month, it_datetime.year))
        idx += 1
        if idx >= len(holidays_list):
            idx = 0
            year += 1
        it_datetime = datetime.datetime(year=year, month=holidays_list[idx][1], day=holidays_list[idx][0])

    return T, T_labels


def _adjust_fig_right_if_needed(fig):
    fig_x_side = fig.get_size_inches()[0]
    adjustment = 0.6 + 0.05*(fig_x_side-8)/4.0 if fig_x_side >= 8 else 0.6
    if adjustment < 1.0:
        fig.subplots_adjust(right=adjustment)

def _is_fig_hires(fig):
    return fig.get_size_inches()[0] >= 18


@savable(default_save=True, default_path_to_save="rating_violinplot.png")
@annotatable
def draw_rating_violinplot(data, **kwargs):
    fig = plt.figure(figsize=kwargs["figsize"] if "figsize" in kwargs else (16, 24))
    ax = plt.subplot(111)
    res = ax.violinplot(data, points=150, widths=0.75, showmeans=True, showmedians=True)
    for stat, hint in zip(["cmeans", "cmedians"], [u"Средний рейтинг", u"Медианный рейтинг"]):
        dot1 = res[stat]._paths[0].vertices[0]
        dot2 = res[stat]._paths[0].vertices[1]
        anchor = ((dot1[0] + dot2[0])/2, (dot1[1] + dot2[1])/2)
        ax.annotate(hint, xy=anchor)
    ax.set_title(u"Распределение рейтинга постов на 15 страницах лучшего")
    ax.set_xticks([])
    ax.set_ylabel(u"Рейтинг")
    ax.set_yticks(np.arange(0, max(data), 1000))


@savable(default_save=True, default_path_to_save="tags_correlation_heatmat.png")
def draw_heat_square_matrix(matrix, labels, **kwargs):

    fig = plt.figure(figsize=kwargs["figsize"] if "figsize" in kwargs else (14, 14))
    ax = plt.subplot(111)
    heatmap = ax.pcolor(matrix, cmap=plt.cm.Blues, alpha=0.8)

    ax.set_frame_on(False)
    ax.set_yticks(np.arange(matrix.shape[0]) + 0.5, minor=False)
    ax.set_xticks(np.arange(matrix.shape[1]) + 0.5, minor=False)
    ax.invert_yaxis()
    ax.xaxis.tick_top()
    ax.set_xticklabels(labels, minor=False)
    ax.set_yticklabels(labels, minor=False)
    plt.xticks(rotation=90)
    ax.grid(False)
    ax = plt.gca()

    for t in ax.xaxis.get_major_ticks():
        t.tick1On = False
        t.tick2On = False
    for t in ax.yaxis.get_major_ticks():
        t.tick1On = False
        t.tick2On = False

    fig.subplots_adjust(top=0.85, left=0.15)


@enforce_kwargs({"path_to_save", "should_save", "hlines", "vlines", "captions", "figsize", "bars_threshold"})
@savable(default_save=True, default_path_to_save="rating_bar_chart.png")
def draw_rating_bar_chart(data_dictionary, bars_threshold=60, **kwargs):

    hlines = []
    if len(data_dictionary) < bars_threshold:
        tags = sorted(list(data_dictionary.keys()))
    else:
        xy_sorted = [t[0] for t in sorted(list(data_dictionary.items()), key=lambda t: t[1])]
        border_tags = []
        tags = [t for t in xy_sorted[:bars_threshold//2]]
        border_tags.append(xy_sorted[0])
        border_tags.append(xy_sorted[bars_threshold//2-1])
        tags.extend([t for t in xy_sorted[-bars_threshold//2:]])
        border_tags.append(xy_sorted[-bars_threshold//2])
        border_tags.append(xy_sorted[-1])
        for tag in border_tags:
            hlines.append([
                0, data_dictionary[tag], "{0:.2f}".format(data_dictionary[tag])
            ])
    y = [data_dictionary[tag] for tag in tags]

    ind = np.arange(len(tags))
    width = 0.5

    fig = plt.figure(figsize=kwargs["figsize"] if "figsize" in kwargs else (44, 12))
    ax = plt.subplot(111)
    rects1 = ax.bar(ind, y, width, color='b')

    if hlines:
        for x, y, text in hlines:
            ax.axhline(y, color='k', linestyle='--')
            ax.annotate(text, xy=(x + width, y + 10))

    ax.set_ylabel(u'Рейтинг')
    ax.set_title(u'Рейтинг по тегам')
    ax.set_xticks(ind + width / 2)
    ax.set_xticklabels(tags)
    plt.xticks(rotation=90)
    fig.subplots_adjust(bottom=0.2 if fig.get_size_inches()[1] >= 12 else 0.25)


@enforce_kwargs({"path_to_save", "should_save", "x_ticks", "hlines", "vlines", "captions", "figsize"})
@savable(default_save=True, default_path_to_save="rating_plot.png")
@annotatable
def draw_post_number_logplot(T, RR, labels, **kwargs):
    fig = plt.figure(figsize=kwargs["figsize"] if "figsize" in kwargs else (24, 14))
    _adjust_fig_right_if_needed(fig)
    ax = plt.subplot(111)
    for R, label in zip(RR, labels):
        ax.semilogy(T, R, label=label)
    ax.set_ylabel(u'Количество постов')
    ax.set_xlabel(u'Рейтинг')
    ax.set_title(u'Логарифмический рейтинг количества постов')
    if "x_ticks" in kwargs:
        ax.set_xticks(kwargs["x_ticks"])
    plt.grid(True)
    plt.xticks(rotation=90)
    bbox_x_anchor = 1.025
    ax.legend(bbox_to_anchor=(bbox_x_anchor, 1), loc=2, borderaxespad=0.)
    if fig.get_size_inches()[1] <= 12:
        fig.subplots_adjust(bottom=0.2)


@enforce_kwargs({"begin_time", "end_time", "path_to_save", "should_save", "hlines", "vlines", "captions", "figsize"})
@savable(default_save=True, default_path_to_save="rating_plot.png")
@annotatable
def draw_rating_plot(T, RR, labels, **kwargs):
    fig = plt.figure(figsize=kwargs["figsize"] if "figsize" in kwargs else (24, 14))
    _adjust_fig_right_if_needed(fig)
    ax = plt.subplot(111)
    for R, label in zip(RR, labels):
        ax.plot(T, R, label=label)
    ax.set_ylabel(u'Доля постов')
    ax.set_xlabel(u'Время')
    ax.set_title(u'Рейтинг по тегам')
    if "begin_time" in kwargs and "end_time" in kwargs:
        begin_datetime = datetime.datetime.fromtimestamp(kwargs["begin_time"])
        end_datetime = datetime.datetime.fromtimestamp(kwargs["end_time"])
        T, T_labels = _generate_time_labels(begin_datetime, end_datetime)
        ax.set_xticks(T)
        ax.set_xticklabels(T_labels)
    plt.xticks(rotation=90)
    bbox_x_anchor = 1.025
    ax.legend(bbox_to_anchor=(bbox_x_anchor, 1), loc=2, borderaxespad=0.)
    if fig.get_size_inches()[1] <= 12:
        fig.subplots_adjust(bottom=0.2)


@savable(default_save=True, default_path_to_save="rating_hourly.png")
def draw_rating_hourly(T, R, N, **kwargs):

    fig = plt.figure(figsize=kwargs["figsize"] if "figsize" in kwargs else (24, 12))
    _adjust_fig_right_if_needed(fig)
    ax = plt.subplot(111)
    ax.plot(T, R, label=u'Средний рейтинг')
    ax.set_title(u"Рейтинг по дням недели")
    ax.set_ylabel('Средний рейтинг')

    ax_twin = ax.twinx() # HERE WE USE twinx() to get a scaled yaxis
    ax_twin.plot(T, N, 'r', label=u'Количество постов')
    ax_twin.set_ylabel('Количество постов')

    T_ticks = np.arange(0, 24*60*60 + 60*60, 60*60)
    T_ticks_labels = ["{0:02d} ч".format(x) for x in range(24)] + ["00 ч"]
    ax.set_xlim((0, 24*60*60))
    ax.set_xticks(T_ticks)
    ax.set_xticklabels(T_ticks_labels, rotation=90)

    is_hires = _is_fig_hires(fig)
    axv_line_divider = 2 if is_hires else 4
    bbox_x_anchor = 1.05 if is_hires else 1.1
    for i, x in enumerate(T_ticks):
        if not i % axv_line_divider:
            ax.axvline(x, color='k', linestyle='--')
    ax.legend(bbox_to_anchor=(bbox_x_anchor, 1), loc=2, borderaxespad=0.)
    ax_twin.legend(bbox_to_anchor=(bbox_x_anchor, 0.9), loc=2, borderaxespad=0.)


@savable(default_save=True, default_path_to_save="rating_daily.png")
def draw_rating_daily(T, R, N, **kwargs):

    fig = plt.figure(figsize=kwargs["figsize"] if "figsize" in kwargs else (24, 12))
    _adjust_fig_right_if_needed(fig)
    ax = plt.subplot(111)
    ax.plot(T, R, label=u'Средний рейтинг')
    ax.set_title(u"Рейтинг по дням недели")
    ax.set_ylabel(u'Средний рейтинг')

    ax_twin = ax.twinx() # HERE WE USE twinx() to get a scaled yaxis
    ax_twin.plot(T, N, 'r', label=u'Количество постов')
    ax_twin.set_ylabel('Количество постов')

    T_ticks = np.arange(0, 7*24*60*60 + 6*60*60, 6*60*60)
    T_ticks_labels = [x[0] + " " + x[1] for x in
                      product(
                          ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
                          ["00:00", "06:00", "12:00", "18:00"]
                      )] + ["Пн 00:00"]
    ax.set_xlim((0, 7*24*60*60))
    ax.set_xticks(T_ticks)
    ax.set_xticklabels(T_ticks_labels, rotation=90)

    is_hires = _is_fig_hires(fig)
    axv_line_divider = 2 if is_hires else 4
    bbox_x_anchor = 1.05 if is_hires else 1.1
    for i, x in enumerate(T_ticks):
        if not i % axv_line_divider:
            ax.axvline(x, color='k', linestyle='--')
    ax.legend(bbox_to_anchor=(bbox_x_anchor, 1), loc=2, borderaxespad=0.)
    ax_twin.legend(bbox_to_anchor=(bbox_x_anchor, 0.9), loc=2, borderaxespad=0.)


@savable(default_save=True, default_path_to_save="rating_monthly.png")
def draw_rating_monthly(T, R, N, **kwargs):

    fig = plt.figure(figsize=kwargs["figsize"] if "figsize" in kwargs else (48, 12))
    _adjust_fig_right_if_needed(fig)
    ax = plt.subplot(111)
    ax.plot(T, R, label=u'Средний рейтинг')
    ax.set_title(u"Рейтинг по дням месяца")
    ax.set_ylabel('Средний рейтинг')

    ax_twin = ax.twinx() # HERE WE USE twinx() to get a scaled yaxis
    ax_twin.plot(T, N, 'r', label=u'Количество постов')
    ax_twin.set_ylabel('Количество постов')

    T_ticks = np.arange(0, 30*24*60*60 + 60*60, 24*60*60)
    T_ticks_labels = [str(i+1) for i in range(30)]
    ax.set_xlim((0, 29*24*60*60))
    ax.set_xticks(T_ticks)
    ax.set_xticklabels(T_ticks_labels, rotation=90)

    is_hires = _is_fig_hires(fig)
    axv_line_divider = 2 if is_hires else 4
    bbox_x_anchor = 1.05 if is_hires else 1.1
    for i, x in enumerate(T_ticks):
        if not i % axv_line_divider:
            ax.axvline(x, color='k', linestyle='--')
    ax.legend(bbox_to_anchor=(bbox_x_anchor, 1), loc=2, borderaxespad=0.)
    ax_twin.legend(bbox_to_anchor=(bbox_x_anchor, 0.9), loc=2, borderaxespad=0.)


@savable(default_save=True, default_path_to_save="tsne_result.png")
def draw_tsne_result(tsne_affinity_coords, labels_list=None, **kwargs):
    fig = plt.figure(figsize=(20, 20))
    ax = plt.axes(frameon=False)
    plt.axis('off')
    if labels_list is None:
        plt.scatter(tsne_affinity_coords[:, 0], tsne_affinity_coords[:, 1])
    else:
        unique_labels = set(labels_list)
        colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))
        for k, col in zip(unique_labels, colors):
            if k == -1:
                col = 'k'  # Black used for noise.

            class_member_mask = (labels_list == k)

            xy = tsne_affinity_coords[class_member_mask]
            plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=col,
                     markeredgecolor='k', markersize=5)

            mean_x = np.mean(xy[:, 0])
            mean_y = np.mean(xy[:, 1])
            plt.text(mean_x, mean_y, str(k))