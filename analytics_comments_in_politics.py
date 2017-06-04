import json
import os
import pickle
from math import sqrt

from sklearn.cluster import DBSCAN
import numpy as np
from sklearn.manifold import TSNE

from drawing import draw_tsne_result
from performance.caching import save_code_based_cache


compute_interuser_affinity_configs = {
    "default" : {
        "post_value" : 10.0,
        "comment_value" : 1.0,
        "user_weight_threshold" : 3.0,
        "comment_to_post_author_value" : 0.3,
        "comment_to_all_comments_value" : 0.2,
        "comment_to_comment_value" : 0.1
    },
    "uniform" : {
        "post_value" : 10.0,
        "comment_value" : 1.0,
        "user_weight_threshold" : 3.0,
        "comment_to_post_author_value" : 0.0,
        "comment_to_all_comments_value" : 0.0,
        "comment_to_comment_value" : 0.2
    }
}

RESULT_FOLDER = "politics_comments"


def add_in_weights_dict(data, username, weight):
    if username in data:
        data[username] += weight
    else:
        data[username] = weight

def get_users_for_record(record):
    usernames = set()
    usernames.add(record["author"])
    for comment in record["comments"]:
        usernames.add(comment["user"])
    return usernames

def get_posts_for_users(data, filter_usernames):
    posts = []
    intersection_users = []
    for i, record in enumerate(data.values()):
        current_usernames = get_users_for_record(record)
        current_intersection_users = filter_usernames.intersection(current_usernames)
        if len(current_intersection_users) > 0:
            posts.append(record)
            intersection_users.append(current_intersection_users)
    return posts, intersection_users

@save_code_based_cache("politics_users.pkl")
def get_weight_filtered_users(data, post_weight, comment_weight, threshold, **kwargs):
    users = {}
    for record in data.values():
        current_post_users = {}
        add_in_weights_dict(users, record["author"], post_weight)
        add_in_weights_dict(current_post_users, record["author"], 1)
        for comment in record["comments"]:
            user = comment["user"]
            divider = sqrt(1 + current_post_users[user]) if user in current_post_users else 1.0
            add_in_weights_dict(users, record["author"], comment_weight/divider)
            add_in_weights_dict(current_post_users, record["author"], 1)
    return {k: v for (k, v) in users.items() if v > threshold}


def traverse_comments_branch(affinity_mat, comment_to_comment_value, users_weights, users_names, record, user_name, user_idx, author_name, author_idx, current_comment, current_depth):
    parent_comment = None
    current_depth += 1
    try:
        parent = current_comment["parent"]
        if parent != "0":
            parent_comment = next(c for c in record["comments"] if (c["id"] == "comment_" + parent))
            parent_name = parent_comment["user"]
            parent_idx = users_names.index(parent_comment["user"])
            if parent_idx == user_idx:
                raise ValueError
        else:
            parent_name = author_name
            parent_idx = author_idx
        affinity_mat[parent_idx, user_idx] += comment_to_comment_value/sqrt(current_depth)*(1.0/users_weights[parent_name] + 1.0/users_weights[user_name])
        affinity_mat[user_idx, parent_idx] += comment_to_comment_value/sqrt(current_depth)*(1.0/users_weights[parent_name] + 1.0/users_weights[user_name])
    except StopIteration:
        pass
    except ValueError:
        pass
    if parent_comment is not None:
        traverse_comments_branch(affinity_mat, comment_to_comment_value, users_weights, users_names, record, user_name, user_idx, author_name, author_idx, parent_comment, current_depth)


@save_code_based_cache("politics_interuser_affinity_mat.pkl")
def compute_interuser_affinity(data, users_weights, users_names, comment_to_post_author_value, comment_to_all_comments_value, comment_to_comment_value, **kwargs):
    print("Computing interuser affinity")

    affinity_mat = np.zeros(shape=(len(users_names), len(users_names)))

    l = len(data.values())
    all_commenters_idxes = set()
    for i, record in enumerate(data.values()):
        print("Processing affinity for {}/{} post".format(i + 1, l))
        try:
            author_name = record["author"]
            author_idx = users_names.index(author_name)
        except ValueError:
            continue
        for comment in record["comments"]:
            try:
                user_name = comment["user"]
                user_idx = users_names.index(user_name)
                affinity_mat[user_idx, author_idx] += comment_to_post_author_value*(1.0/users_weights[user_name] + 1.0/users_weights[author_name])
                affinity_mat[author_idx, user_idx] += comment_to_post_author_value*(1.0/users_weights[user_name] + 1.0/users_weights[author_name])
                all_commenters_idxes.add((user_idx, user_name))
            except ValueError:
                continue
            traverse_comments_branch(affinity_mat, comment_to_comment_value, users_weights, users_names, record, user_name, user_idx, author_name, author_idx, comment, 0)
    all_commenters_idxes = list(all_commenters_idxes)
    for i, (idx1, name1) in enumerate(all_commenters_idxes):
        for (idx2, name2) in all_commenters_idxes[:i+1]:
            affinity_mat[idx1, idx2] += comment_to_all_comments_value*(1.0/users_weights[name1] + 1.0/users_weights[name2])
            affinity_mat[idx2, idx1] += comment_to_all_comments_value*(1.0/users_weights[name1] + 1.0/users_weights[name2])
    return users_weights, users_names, affinity_mat


@save_code_based_cache("politics_tsne_clusters.pkl")
def cluster_users_with_tsne(distance_mat, perplexity, eps, min_samples, **kwargs):
    model = TSNE(metric="precomputed", n_components=2, random_state=0, perplexity=perplexity)
    tsne_distance = model.fit_transform(distance_mat)
    db = DBSCAN(eps=eps, min_samples=min_samples).fit(tsne_distance)
    labels_list = db.labels_
    return tsne_distance, labels_list


@save_code_based_cache("politics_labeled_users.pkl")
def split_users(users_names, labels, **kwargs):
    labeled_users = {}
    unique_labels = set(labels)
    for label in unique_labels:
        labeled_users[label] = set([user_name for user_name, user_label in zip(users_names, labels) if label == user_label])
    return labeled_users


@save_code_based_cache("politics_intersection_analysis.pkl")
def intersection_analysis(users_names, labels_list, **kwargs):

    number_of_clusters = len(set(labels_list))
    labeled_users = split_users(users_names, labels_list, save_code=name)

    suspicious_result = []
    for i, (cluster_no, users) in enumerate(labeled_users.items()):
        print("Analyzing {}/{} cluster".format(i+1, number_of_clusters))
        if int(cluster_no) == -1:
            continue

        posts, intersection_users = get_posts_for_users(data, users)
        max_intersection_number = max([len(u) for u in intersection_users])

        suspicious_posts_info = []
        for post, post_users in zip(posts, intersection_users):
            if len(post_users) > 1:
                suspicious_posts_info.append((post["link"], len(post_users), list(post_users)))

        suspicious_result.append(
            {
                "cluster_no" : int(cluster_no),
                "number_of_posts_with_users" : len(intersection_users),
                "max_intersection_number" : max_intersection_number,
                "users_n" : len(users),
                "users" : list(users),
                "suspicious_posts_len" : len(suspicious_posts_info),
                "suspicious_posts_info" : [] if int(cluster_no) == -1 else suspicious_posts_info,
                "users_to_posts_ratio" : len(suspicious_posts_info)/len(users),
                "suspiciousness_ratio" : len(suspicious_posts_info)/len(intersection_users)
            }
        )

    suspicious_result = sorted(suspicious_result, key=lambda x: -x["suspiciousness_ratio"])
    return suspicious_result


if __name__ == "__main__":

    print("Loading data")
    with open("full_data.pkl", "rb") as handle:
        data = pickle.load(handle)

    for name, params in compute_interuser_affinity_configs.items():

        print("Config {}".format(name))

        print("Filtering users by weight")
        users_weights = get_weight_filtered_users(data,
                params["post_value"],
                params["comment_value"],
                params["user_weight_threshold"],
                save_code=name)
        users_names = sorted([k for (k, v) in users_weights.items()])
        print("{} users".format(len(users_names)))

        print("Computing/loading affinity")
        users_weights, users_names, affinity_mat = compute_interuser_affinity(data,
                users_weights,
                users_names,
                params["comment_to_post_author_value"],
                params["comment_to_all_comments_value"],
                params["comment_to_comment_value"],
                save_code=name)

        distance_mat = -affinity_mat + np.max(affinity_mat) + 0.001
        np.fill_diagonal(distance_mat, 0)

        print("Fitting")

        tsne_results = []
        perplexity_list = [2.0, 4.0, 8.0]
        for perplexity in perplexity_list:
            tsne_results.append(cluster_users_with_tsne(distance_mat, perplexity, 0.5, 7, save_code=name+str(perplexity)))

        print("Drawing")

        for idx, (tsne_distance, labels_list) in enumerate(tsne_results):
            path_to_save = os.path.join(RESULT_FOLDER, name + "_tsne_" + str(perplexity_list[idx]).replace(".", "_"))
            draw_tsne_result(tsne_distance, None, path_to_save=path_to_save)
            path_to_save = os.path.join(RESULT_FOLDER, name + "_tsne_clustered_" + str(perplexity_list[idx]).replace(".", "_"))
            draw_tsne_result(tsne_distance, labels_list, path_to_save=path_to_save)

        print("Analyzing size of clusters")

        labels_list = tsne_results[-1][1]
        suspicious_result = intersection_analysis(users_names, labels_list, save_code=name)

        path_to_save = os.path.join(RESULT_FOLDER, "politics_suspicious_" + name + ".txt")
        with open(path_to_save, 'w') as fp:
            json.dump(suspicious_result, fp, indent=4)

