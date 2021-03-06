import os
import sys
import json
import pandas as pd
import gensim
import logging
import random
from scipy.stats import percentileofscore


def load_model(embeddings_file):
    """
    This function, unifies various standards of word embedding files.
    It automatically determines the format by the file extension
    and loads it from the disk correspondingly.
    :param embeddings_file: path to the file
    :return: the loaded model
    """
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    if not os.path.isfile(embeddings_file):
        raise FileNotFoundError("No file called {file}".format(file=embeddings_file))
    # Determine the model format by the file extension
    # Binary word2vec file:
    if embeddings_file.endswith('.bin.gz') or embeddings_file.endswith('.bin'):
        emb_model = gensim.models.KeyedVectors.load_word2vec_format(
            embeddings_file, binary=True, unicode_errors='replace')
    # Text word2vec file:
    elif embeddings_file.endswith('.txt.gz') or embeddings_file.endswith('.txt') \
            or embeddings_file.endswith('.vec.gz') or embeddings_file.endswith('.vec'):
        emb_model = gensim.models.KeyedVectors.load_word2vec_format(
            embeddings_file, binary=False, unicode_errors='replace')
    else:  # Native Gensim format?
        emb_model = gensim.models.KeyedVectors.load(embeddings_file)
    emb_model.init_sims(replace=True)

    return emb_model


def get_models_by_decade(cur_decade: int, kind: str, lang='rus'):
    if kind not in ['regular', 'incremental']:
        raise ValueError
    if lang not in ['rus', 'nor', 'eng']:
        raise ValueError

    if kind == "regular":
        model = load_model('models/{lang}/{decade}.model'.format(lang=lang, decade=cur_decade))
    else:
        model = load_model('models/{lang}/{decade}_incremental.model'.format(
            lang=lang, decade=cur_decade))

    return model


def delete_lowfrequent(wordlist, threshold, vocablist):
    newlist = set()  # sets are generally faster than lists, and we don't need order here
    for word in wordlist:
        hit = False
        for vocab in vocablist:
            if vocab[word].count < threshold:
                hit = True
                break
        if hit:
            continue
        newlist.add(word)

    return newlist


def get_freqdict(wordlist, vocablist, corpus_size, return_percentiles=True):
    all_freqs = []
    word_freq = {}
    for word in wordlist:
        counts = [vocab[word].count for vocab in vocablist]
        frequency = [counts[i] / corpus_size[i] for i in range(len(vocablist))]
        mean_frequency = sum(frequency) / len(frequency)
        all_freqs.append(mean_frequency)
        word_freq[word] = mean_frequency

    if return_percentiles:
        percentiles = {}
        for word in wordlist:
            percentiles[word] = int(percentileofscore(all_freqs, word_freq[word]))
        return percentiles

    else:
        return word_freq


def output_results(evaluative_dict, rest_dict):
    rest_dict_inv = {}

    for key, value in rest_dict.items():
        rest_dict_inv.setdefault(value, []).append(key)

    df = pd.DataFrame()
    finallist = set()
    missing_perc = []

    for i in evaluative_dict:
        perc = evaluative_dict[i]
        try:
            sl = random.sample(rest_dict_inv[perc], 2)
        except (ValueError, KeyError):
            missing_perc.append(evaluative_dict[i])
            continue
        for el in sl:
            finallist.add(el)
            rest_dict_inv[perc].remove(el)

    df['WORD'] = list(finallist)

    return df  # , missing_perc


def get_len(current_corpus, lens_file, lang='rus'):
    if lang not in ['rus', 'nor', 'eng']:
        raise ValueError

    with open(lens_file) as f:
        length_data = json.load(f)

    corpus_size = length_data[lang][current_corpus]

    return corpus_size


if __name__ == '__main__':
    root = 'adjectives/'

    INCREMENTAL = False
    START_DECADE = 1960

    models_regular = []
    if INCREMENTAL:
        models_incremental = []
    corpus_lens = []

    language = sys.argv[1]  # one of ['eng', 'rus', 'nor']

    os.makedirs(root + 'rest/' + language, exist_ok=True)

    corpora_sizes_file = sys.argv[4]

    for decade in range(START_DECADE, 2010, 10):
        corpus_len = get_len(str(decade), corpora_sizes_file, lang=language)
        corpus_lens.append(corpus_len)

        model_regular = get_models_by_decade(decade, 'regular', lang=language)
        models_regular.append(model_regular)
        if INCREMENTAL:
            model_incremental = get_models_by_decade(decade, 'incremental', lang=language)
            models_incremental.append(model_incremental)

    vocabs_regular = [model.vocab for model in models_regular]
    if INCREMENTAL:
        vocabs_incremental = [model.vocab for model in models_incremental]

    intersec_regular = set.intersection(*map(set, vocabs_regular))
    print('Size of shared vocabulary, regular:', len(intersec_regular), file=sys.stderr)
    if INCREMENTAL:
        intersec_incremental = set.intersection(*map(set, vocabs_incremental))
        print('Size of shared vocabulary, incremental:', len(intersec_incremental), file=sys.stderr)

    print('Loading evaluative vocabulary...', file=sys.stderr)
    words_regular = []
    if INCREMENTAL:
        words_incremental = []
    eval_adj = pd.read_csv('datasets/{}/{}_sentiment.csv'.format(
        language, language))

    tag = 'ADJ'  # We work only with adjectives, no need to specify it each time

    all_eval_adj = set()  # All evaluative adjectives, independent of models

    for line in eval_adj['WORD']:
        voc_word = line + '_' + tag
        all_eval_adj.add(voc_word)
        if voc_word in intersec_regular:
            words_regular.append(voc_word)
        if INCREMENTAL:
            if voc_word in intersec_incremental:
                words_incremental.append(voc_word)

    print('Filtering by frequency...', file=sys.stderr)
    words_regular_filtered = delete_lowfrequent(words_regular, int(sys.argv[2]), vocabs_regular)
    if INCREMENTAL:
        words_incremental_filtered = delete_lowfrequent(words_incremental, int(sys.argv[2]),
                                                        vocabs_incremental)

    # print(len(words_regular_filtered), len(words_incremental_filtered))
    # print(words_regular_filtered[:10], words_incremental_filtered[:10])

    wordfreq_regular = get_freqdict(words_regular, vocabs_regular, corpus_lens)
    wordfreq_regular_filtered = get_freqdict(words_regular_filtered, vocabs_regular, corpus_lens)
    if INCREMENTAL:
        wordfreq_incremental = get_freqdict(words_incremental, vocabs_incremental, corpus_lens)
        wordfreq_incremental_filtered = get_freqdict(words_incremental_filtered,
                                                     vocabs_incremental, corpus_lens)

    print('Generating fillers...', file=sys.stderr)
    rest_regular = set()

    for voc_word in intersec_regular:
        if voc_word.endswith(tag) and voc_word not in all_eval_adj:
            rest_regular.add(voc_word)
    if INCREMENTAL:
        rest_incremental = set()
        for voc_word in intersec_incremental:
            if voc_word.endswith(tag) and voc_word not in all_eval_adj:
                rest_incremental.add(voc_word)

    rest_regular_filtered = delete_lowfrequent(rest_regular, int(sys.argv[2]), vocabs_regular)

    if INCREMENTAL:
        rest_incremental_filtered = delete_lowfrequent(rest_incremental, int(sys.argv[2]),
                                                       vocabs_incremental)

    restfreq_regular = get_freqdict(rest_regular, vocabs_regular, corpus_lens)
    restfreq_regular_filtered = get_freqdict(rest_regular_filtered, vocabs_regular, corpus_lens)

    if INCREMENTAL:
        restfreq_incremental = get_freqdict(rest_incremental, vocabs_incremental, corpus_lens)
        restfreq_incremental_filtered = get_freqdict(rest_incremental_filtered, vocabs_incremental,
                                                     corpus_lens)

    if sys.argv[3] == 'with_distribution':
        print('Sampling proper distribution...', file=sys.stderr)
        output_results(wordfreq_regular, restfreq_regular).to_csv(root + 'rest/' + language + '/'
                                                                  + sys.argv[3] + '/regular.csv')
        output_results(wordfreq_regular_filtered, restfreq_regular_filtered).to_csv(
            root + 'rest/' + language + '/' + sys.argv[3] + '/regular_filtered_' + sys.argv[
                2] + '.csv')
        if INCREMENTAL:
            output_results(wordfreq_incremental, restfreq_incremental).to_csv(
                root + 'rest/' + language + '/' + sys.argv[3] + '/incremental.csv')
            output_results(wordfreq_incremental_filtered, restfreq_incremental_filtered).to_csv(
                root + 'rest/' + language + '/' + sys.argv[3] + '/incremental_filtered_' + sys.argv[
                    2] + '.csv')
    else:
        rest_reg_df = pd.DataFrame()
        rest_reg_df['WORD'] = sorted(list(rest_regular))
        rest_reg_df.to_csv(root + 'rest/' + language + '/regular.csv')
        rest_reg_fil_df = pd.DataFrame()
        rest_reg_fil_df['WORD'] = sorted(list(rest_regular_filtered))
        rest_reg_fil_df.to_csv(
            root + 'rest/' + language + '/regular_filtered_' + sys.argv[2] + '.csv')
        if INCREMENTAL:
            rest_incr_df = pd.DataFrame()
            rest_incr_df['WORD'] = sorted(list(rest_incremental))
            rest_incr_df.to_csv(root + 'rest/' + language + '/incremental.csv')
            rest_incr_fil_df = pd.DataFrame()
            rest_incr_fil_df['WORD'] = sorted(list(rest_incremental_filtered))
            rest_incr_fil_df.to_csv(
                root + 'rest/' + language + '/incremental_filtered_' + sys.argv[2] + '.csv')

    eval_filtered_regular = pd.DataFrame()
    eval_filtered_regular['WORD'] = sorted(list(words_regular_filtered))
    eval_filtered_regular.to_csv('{}{}_regular_filtered_{}.csv'.format(root, language, sys.argv[2]))
    if INCREMENTAL:
        eval_filtered_incremental = pd.DataFrame()
        eval_filtered_incremental['WORD'] = sorted(list(words_incremental_filtered))
        eval_filtered_incremental.to_csv('{}{}_incremental_filtered_{}.csv'.format(
            root, language, sys.argv[2]))
