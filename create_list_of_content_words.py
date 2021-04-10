import sys
import os
cwd = os.getcwd()
dir_for_working_code = os.path.join(cwd, 'working-code')
sys.path.append(os.path.abspath(dir_for_working_code))
from ToDosLogger import *
from Sarahs_helper_functions import *
logger = ToDosLogger(LOG_FILE)
# ------------------------------------------------------------------------------

corpus = readDirectoryAsCorpus("corpus")
normalized = removeHyphensAndPunctuation(corpus)
top = corpus[0:4000]

STOP_WORDS_LIST = getStopwords()
content_words = getContentWordsList()

bow_dict, reduced_corpus = updateBagOfWordsFromString(corpus, STOP_WORDS_LIST, content_words)

bowProcessingInfo()
# ------------------------------------------------------------------------------

iteration_count = len(bow_dict)

while iteration_count > 40:
    for i in range(40):
        bow_dict, content_words, STOP_WORDS_LIST = processOneBOWItem(corpus, bow_dict, content_words, STOP_WORDS_LIST)
        iteration_count -= 1
    bow_dict, reduced_corpus = updateBagOfWordsFromList(reduced_corpus, STOP_WORDS_LIST, content_words)
    informAboutCurrentProgress(bow_dict,  " ".join(reduced_corpus))

# ------------------------------------------------------------------------------
print("\n---\nLast 40!\n---\n")
last_items = len(bow_dict)
while last_items:
    bow_dict, content_words, STOP_WORDS_LIST = processOneBOWItem(corpus, bow_dict, content_words, STOP_WORDS_LIST)
    last_items -= 1
bow_dict, reduced_corpus =  updateBagOfWordsFromList(reduced_corpus, STOP_WORDS_LIST, content_words)
informAboutCurrentProgress(bow_dict,  " ".join(reduced_corpus))
# ------------------------------------------------------------------------------

printMostFrequentContentWords(content_words)
quitBOWProcessing(bow_dict, STOP_WORDS_LIST, content_words)
