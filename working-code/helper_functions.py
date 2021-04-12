
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

import glob # to read corpus from multiple .txt files in directory
import string # for removing punctuation
from collections import Counter # for bow creation

import regex as re # sudo -H python3 -m pip install regex
from tqdm import tqdm # to display a progress bar

from ToDosLogger import *
from cltk_based_text_processing import tokenizeLatinWords, jv_replace, normalizeLatinWordsInNonstandardGlyphs

# ------------------------------------------------------------------------------
# general helper functions for setting up the corpus
# ------------------------------------------------------------------------------

def readOneWordPerLineFileAsList(file_path):
    """
    Accepts the path to a `.txt` file with one word per line and reads it in as a list.
    """
    with open(file_path,  'r+') as f: #TODO opens in read mode, better a+?
        word_list = f.read().splitlines()
        word_set = set(word_list)
        word_list = list(word_set)
        return word_list

# ------------------------------------------------------------------------------
def writeListAsOneWordPerLineFile(word_list, file_to_write_path):
    """
    Accepts a list and the path to a `.txt` file where the list items will be sroted one per line.
    """
    file = open(file_to_write_path, "w+") # open file in overwrite mode
    words = [w for w in word_list if w != '']
    while words: # empty list is implicity boolean in python
        for word in words:
            file.write(word + "\n")
        break
    file.close()


# ------------------------------------------------------------------------------
def readDirectoryAsCorpus(directory):
    """
    Pass a directory name to this function and it will read all its contained `.txt` files as a corpus.

    The resulting corpus is all the texts combined together in one string.
    Will show current progss with a progress bar.
    """
    txt_files = glob.glob(directory + "/*.txt")
    corpus = ''
    # add together all the texts from the directory as a common corpus
    files = tqdm(txt_files)
    for file in files:
        files.set_description("Reading %s" % file)
        with open(file, 'rt') as current_text:
            text_as_string = current_text.read()
            corpus = corpus + ' ' + text_as_string
    return corpus

# ------------------------------------------------------------------------------
def getCorpusSize(corpus):
    """
    Takes the corpus as a string and returns the number of unique items.
    """
    words = corpus.split()
    total_words = len(words)
    unique_items = set(words)
    unique_words = len(unique_items)
    print("Corpus has " + str(total_words) + " words in total (TOKENS), with " \
    + str(unique_words) + " distinct values (TYPES).\n")
    return unique_words

# ------------------------------------------------------------------------------
# Progress Bar adapted from
# https://stackoverflow.com/questions/3160699/python-progress-bar
# ------------------------------------------------------------------------------
def showProgressBar(total_corpus_len, total_bow_len, prefix="", size=60):
    """
    This is a static progress bar adapted from a StackOverflow answer:
    https://stackoverflow.com/questions/3160699/python-progress-bar
    It will show the progress / difference between the total number of types
    to process in the corpus and the amount left to do.
    The prefix argument currently get overwritten in the function.
    """
    progress = total_bow_len / total_corpus_len
    #print("progress(" + str(progress) + ") = total_bow_len(" + str(total_bow_len) +") / total_corpus_len(" + str(total_corpus_len) + ")")
    todo = (1 - progress)*100 # ist in Prozent, daher 1- ...
    #print("Progress percentage is: " + str(progress))
    #progress_length = int(size/progress)
    #progress_length = int(size/todo)
    progress_length = int((todo/100)*size)
    #print("todo is: " + str(todo) + ", progress_length: " + str(progress_length))
    #print("Progress len = " + str(progress_length))
    prefix = "TODO " + str(int(todo)) + "%"
    print(("%s[%s%s] %i/%i\r" % (prefix, "#"*progress_length, "."*(size-progress_length), \
     total_bow_len, total_corpus_len)))

# ------------------------------------------------------------------------------
def remove_punctuation(text_string):
    """
    Removes punctuation from a given string.
    string.punctuation includes: '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
    """
    text_string = text_string.translate(str.maketrans('', '', string.punctuation))
    return text_string

# ------------------------------------------------------------------------------
def remove_hyphens(corpus):
    """Removes all the words breaks with hyphens.

    Assumes they look like '-\n' and reunites those words.
    Does not account for words compounded with hyphens
    since it is supposed to deal with Latin which shouldn't have those.
    Use this !before! tokenization and !before! removing punctuation,
    as this '-\n' combination will not be present anymore afterwards!
    """
    corpus = corpus.translate(str.maketrans('', '', '-\n'))
    return corpus

# ------------------------------------------------------------------------------
def removeHyphensAndPunctuation(corpus):
    """
    Will normalize by removing hyphens and punctuation.
    """
    corpus = remove_hyphens(corpus)
    corpus = remove_punctuation(corpus)
    return corpus

# ------------------------------------------------------------------------------
def getBagOfWordsFromString(corpus, STOP_WORDS_LIST):
    """
    Creates a bag of words from a corpus (as string). Using CLTK for Latin.

    Will remove linebreak-hyphens and punctuation as well as stopwords.
    WILL NOT lowercase (!) - so truecasing can be done later, if needed.
    """
    normalized = removeHyphensAndPunctuation(corpus)
    #tokens = normalized.split() # this would be the non-Latin/language specific way
    tokens = tokenizeLatinWords(normalized)
    corpus_without_stopwords = removeStopwordsFromTokens(STOP_WORDS_LIST, tokens)
    bow_dict = Counter(corpus_without_stopwords)
    return bow_dict

# ------------------------------------------------------------------------------
def normalizeList(the_list):
    """
    Will normalize a list by removing empty items and duplicates.
    """
    while "" in the_list:
        the_list.remove("")
    unique_values = set(the_list)
    clean_list = list(unique_values)
    return clean_list

# ------------------------------------------------------------------------------
def cleanCorpus(corpus_list):
    """
    Will normalize a corpus (given as list) by removing empty items and those of len > 2.
    """
    while "" in corpus_list:
        corpus_list.remove("")
    corpus_tokens = tqdm(corpus_list)
    corpus_tokens.set_description("Clearning corpus")
    clean_list = [item for item in corpus_tokens if len(item) > 2]
    return clean_list

# ------------------------------------------------------------------------------
def normalizeWord(word):
    """
    Will normalize a word (as string) by removing glyphs, performing jv_replace and lowercasing.
    """
    glyphs_removed = normalizeLatinWordsInNonstandardGlyphs(word)
    jv_replaced = jv_replace(glyphs_removed)
    lowercased = jv_replaced.lower()
    return lowercased


# ------------------------------------------------------------------------------
def removeStopwordsFromTokens(STOP_WORDS_LIST, tokens):
    """
    Removes stopwords from a list of tokens using the STOP_WORDS_LIST.

    Before using this function, be sure to getStopwords() again,
    so the list is up-to-date.
    """
    stop_set = list(set(STOP_WORDS_LIST))
    stop_words = [s for s in stop_set if s != '']
    corpus_tokens = tqdm(tokens)
    corpus_tokens.set_description("Stopword Removal")
    tokens_without_stopwords = [w for w in corpus_tokens if not w in stop_words]
    #tokens_without_stopwords_match = [w for w in corpus_tokens if not w in stop_words]
    #corpus_tokens_norm = tqdm(tokens_without_stopwords_match)
    # ab Vorhandensein eines gewissen Fundus bringt das nix mehr, aber braucht Laufzeit
    #corpus_tokens_norm.set_description("Stopword Removal Normalized")
    #tokens_without_stopwords = [w for w in corpus_tokens_norm if not normalizeWord(w) in stop_words]
    return tokens_without_stopwords

# ------------------------------------------------------------------------------
def getStopwords():
    """
    A function to determine Stopwords given a list from Perseus or another provided list.

    If `stop_word_list.txt` exists and is not empty, those custom stopwords will be used.
    Otherwise, it will set up a list of basic stopwords as seen in PERSEUS_STOPS.
    """
    PERSEUS_STOPS = ' a ab ac ad adhic aliqui aliquae aliquod alicuius alicui aliquo aliqua aliquorum aliquarum aliquibus aliquos aliquas aliqua aliquis aliquid an ante apud at atque aut '\
    ' autem cuius cui cum cur de deinde dum ego enim eram eras erat eramus eratis erant ergo ero eris erit erimus eritis erunt es esse esset essent est estis et etiam '\
    ' etsi ex e fio fis fit fimus fitis fiunt fui fuisti fuit fuimus fuistis fuerunt haud hinc hic haec hoc huius huic hunc hanc hoc hac hi hae haec horum harum his hos has huc iam idem igitur ille illa illud illius illi illum illam illo illae illorum illarum illis illos illas in infra inter '\
    ' interim inde itaque ipse ipsa ipsum ipsius ipsi ipsam ipso ipsae ipsorum ipsarum ipsis ipsos ipsas is ea id eius ei eum eam eo ii eae ea eorum earum iis eos eas ita m magis mihi me meus mea meum mi mei meo meae meam meorum mearum meis meos meas modo mox nam ne nec necque neque '\
    ' nisi non nos nostrum nihil nostri nobis nullus nulla nullum nullius nulli nullo nullae nullam nulli nullae nullibus nullos nullas nunc o ob per possum post pro quae quam quare qui quod quem quos quas quo qua quorum quarum '\
    ' quia quibus quicumque quidem quidquid quilibet quis quid quisnam quisquam '\
    ' quisque quisquis quo quoniam quoque quot quotiens se sed si sic sine sit sint sis simus sive sub sui sum sumus sunt '\
    ' super suus sua suum suo suam talis tale talia tam tamen te tibi trans tu tum tuus tua tuum tuo tuae tuam tui tuorum tuarum tuis tuos tuas ubi uel vel uero vero unus una unum unius uni unam uno ut '\
    'SARAH -que -ve -ne vt causa imprimis velut quasi contra quin econtra '\
    'praeter gratum grata à sat Google ceu amp -ue -ve ubi vbi copia res rem re rerum rei rebus unde vnde'\
    'quidam quaedam quoddam cuiusdam cuidam quendam quandam quodam quadam cujusdam quiddam quorundam quorandam quosdam quasdam quibusdam '\
    'esses quamvis quamuis tantum tanta tanto tanti tantae tantos tantas tanti tantis tante '\
    'omnis omni omne omnem omnium omnibus omnia omnes è cum ad paene '\
    'seu ideo utpote vtpote tot semel vix satis inquit '\
    'sibi se donec sese vni ut uni nostro nostrum nostri noster ideo sui suae sua suam suo suis sui suum suo suorum suarum suis suos suas'
    perseus_stopwords = PERSEUS_STOPS.split()
    stops_list = []
    stops_list = readOneWordPerLineFileAsList("stop_word_list.txt")
    # should create the file if it doesn't exist
    if not stops_list: # i.e. list is empty, add the basic ones from Perseus, otherwise they're already in there!
        stops_list = perseus_stopwords
    stops_list = [x for x in stops_list if x.strip()] # remove empty items
    return stops_list

# ------------------------------------------------------------------------------
# FINIS
# ------------------------------------------------------------------------------
