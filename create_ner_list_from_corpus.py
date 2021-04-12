import sys
import os
cwd = os.getcwd()
dir_for_working_code = os.path.join(cwd, 'working-code')
sys.path.append(os.path.abspath(dir_for_working_code))
from ToDosLogger import *
from helper_functions import *
from cltk_based_text_processing import createNERListFromCorpus
logger = ToDosLogger(LOG_FILE)
# ------------------------------------------------------------------------------

corpus = readDirectoryAsCorpus("corpus")

corpus_ner_list = createNERListFromCorpus(corpus)
declined_ner_list = declineEachWordInList(corpus_ner_list, "NER", logger)

writeListAsOneWordPerLineFile(corpus_ner_list, "NE-in-corpus.txt")
