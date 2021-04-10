
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

import glob # to read corpus from multiple .txt files in directory
import string # for removing punctuation
from collections import Counter # for bow creation

import regex as re # sudo -H python3 -m pip install regex
import unicodedata # for removing ligatures from data in pre-processing
from tqdm import tqdm # to display a progress bar

import cltk # for processing Natural Language Processing of Latin

from ToDosLogger import *

# ------------------------------------------------------------------------------
# general helper functions for setting up the corpus
# ------------------------------------------------------------------------------

def readOneWordPerLineFileAsList(file_path):
    with open(file_path,  'r+') as f: #TODO opens in read mode, better a+?
        word_list = f.read().splitlines()
        word_set = set(word_list)
        word_list = list(word_set)
        return word_list

# ------------------------------------------------------------------------------
def writeListAsOneWordPerLineFile(word_list, file_to_write_path):
    file = open(file_to_write_path, "w+") # open file in overwrite mode
    words = [w for w in word_list if w != '']
    while words: # empty list is implicity boolean in python
        for word in words:
            file.write(word + "\n")
        break
    file.close()

# ------------------------------------------------------------------------------
def writeContentWordDictAsOneWordPerLineFile(content_words_dict, file_to_write_path):
    file = open(file_to_write_path, "w+") # open file in overwrite mode
    for key, value in content_words_dict.items():
        word_count = value[0]
        list_of_forms = " ".join(value[1])
        file.write(key + "," + str(word_count) +  "," + list_of_forms + "\n")
    file.close()

# ------------------------------------------------------------------------------
def readOneWordPerLineFileAsContentWordDict(file_path):
    content_words_dict = {}
    with open(file_path,  'r+') as f: #TODO opens in read mode, better a+?
        lines = f.read().splitlines()
        for line in lines:
            items = line.split(",")
            key = items[0]
            word_count = items[1]
            regex_list = items[2].split(" ")
            content_words_dict[key] = [word_count, regex_list]
        return content_words_dict

# ------------------------------------------------------------------------------
def readDirectoryAsCorpus(directory):
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
    todo = (1 - progress)*100 # ist in Prozent, daher 1- ...
    print("Progress percentage is: " + str(progress))
    #progress_length = int(size/progress)
    progress_length = int(size/todo)
    prefix = "TODO " + str(int(todo)) + "%"
    print(("%s[%s%s] %i/%i\r" % (prefix, "#"*progress_length, "."*(size-progress_length), \
     total_bow_len, total_corpus_len)))

# ------------------------------------------------------------------------------
def informAboutCurrentProgress(bow_dict, corpus):
    original_corpus_length_unique = getCorpusSize(corpus)
    current_bow_size = len(bow_dict)
    print("\nCorpus has [" + str(original_corpus_length_unique) + \
      "] unique values, of which [" + str(current_bow_size) + "] are in the BOW.")
    showProgressBar(original_corpus_length_unique, current_bow_size)

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
def getContentWordsList():
    """
    A function to load content words from a txt file.
    """
    content_words = readOneWordPerLineFileAsContentWordDict("content_words.txt")
    # should create the file if it doesn't exist
    return content_words

# ------------------------------------------------------------------------------
def createNewEntryInContentWordDict(word, count_value, content_words_dict):
    normalized_word_forms = prepareForStopwordList(word)
    normalized_word_forms.append(word) # add the exact word form which was found
    # which might not be normalized - so remains accessible for annotation later
    word_set = set(normalized_word_forms)
    forms_to_add = list(word_set)
    count = count_value # of dict
    lemma = lemmatizeWord(normalizeWord(word))
    #print("In createNewEntryInContentWordDict: key=" + lemma + ", key_count=" + str(count))
    content_words_dict[lemma] = [count, forms_to_add]
    return content_words_dict, forms_to_add

# ------------------------------------------------------------------------------
def addToContentWordEntry(word_form, count_value, content_words_dict):
    key = lemmatizeWord(normalizeWord(word_form)) # list with one item
    key_count = count_value
    #print("In addToContentWordEntry: key=" + key + ", key_count=" + str(key_count))
    if key in content_words_dict:
        new_count = key_count + int(content_words_dict[key][0])
        content_words_dict[key][1].append(word_form)
        new_regexes = content_words_dict[key][1]
        content_words_dict[key] = [new_count, new_regexes]
    return content_words_dict

# ------------------------------------------------------------------------------
def batchUpdateContentWordEntryWordCount(forms_added, bow_dict, content_words_dict):
    total_count = 0
    for word_form in forms_added:
        if word_form in bow_dict:
            count = bow_dict[word_form]
            total_count += count
            bow_dict.pop(word_form)
    key = lemmatizeWord(normalizeWord(word_form)) # list with one item
    if key in content_words_dict:
        regexes = content_words_dict[key][1]
        content_words_dict[key] = [total_count, regexes]
    return content_words_dict, bow_dict


# ------------------------------------------------------------------------------
def normalizeList(the_list):
    while "" in the_list:
        the_list.remove("")
    unique_values = set(the_list)
    clean_list = list(unique_values)
    return clean_list

# ------------------------------------------------------------------------------
def removeProcessedContentWordsFromBOW(tokens, content_words):
    bow_dict_types_list = [value[1] for key, value in content_words.items()]
    bow_types = []
    for types_list in bow_dict_types_list:
        bow_types += types_list
    #print("-----------------> These strings are in the bow removal list..")
    #print(bow_types)
    bow_types = normalizeList(bow_types)

    print("\n---\nTokens before removal of content words: " + str(len(tokens)))
    corpus_tokens = tqdm(tokens)
    corpus_tokens.set_description("Removal of already processed content words")
    tokens_without_normalized_content_words = [w for w in corpus_tokens if not normalizeWord(w) in bow_types]
    tokens_without_content_words = [w for w in tokens_without_normalized_content_words if not w in bow_types]
    print("After: " + str(len(tokens_without_content_words)))
    return tokens_without_content_words

# ------------------------------------------------------------------------------
def addItemToContentWordDictIfNotAlreadyIn(original_word, count_value, content_words, bow_dict):
    finding = [key for key, value in content_words.items() if original_word in value[1]]
    found_normalized = [key for key, value in content_words.items() if normalizeWord(original_word) in value[1]]
    #print(finding)
    #print(found_normalized)
    if finding:
        print("was found - nothing to be done")
        # das sollte hier eig schon gar nicht mehr passieren oder???
        #print(finding)
        # also wunderbar, wir sind doch hier gelandet :D
        bow_dict.pop(original_word)
    elif found_normalized:
        #TODO wozu ist das hier ?
        current_key = found_normalized[0] # only checks the first one - even when there are more finds!
        print("Found in normalized form! Adding original form..")
        content_words = addToContentWordEntry(original_word, count_value, content_words)
        bow_dict.pop(original_word)
    else:
        print("Word wasn't yet in the dict, adding now...")
        content_words, forms_added = createNewEntryInContentWordDict(original_word, \
                                     count_value, content_words)
        content_words, bow_dict = batchUpdateContentWordEntryWordCount(forms_added, bow_dict, content_words)
    #print(content_words)
    return content_words, bow_dict


# ------------------------------------------------------------------------------
def quitBOWProcessing(bow_dict, STOP_WORDS_LIST, content_words):
    # checking whether the list was actually permanently modified...
    #print("\n\nCurrent state of STOPS:")
    #print(" ".join(STOP_WORDS_LIST))
    print("\n---\nWriting this new stopword list to file.")
    updateStopwordList(STOP_WORDS_LIST)
    print("Writing the current state of content words to file.")
    writeContentWordDictAsOneWordPerLineFile(content_words, "content_words.txt")
    print("\n---\nBye for now!")

# ------------------------------------------------------------------------------
def printMostFrequentContentWords(content_words):
    print("\n---\nThose are the lemmata in the content word list so far:")
    sorted_bow = sorted(content_words.items(), key=lambda key: key[0][0])
    for item in sorted_bow:
        print(item)

# ------------------------------------------------------------------------------
def bowProcessingInfo():
    print("\n\n\n----------------")
    print("You will now be prompted to add items to the content words list.")
    print("Say [s/n/-] for STOPS or [k/y/+/ENTER] for KEEP.\n[q] to quit.")
    print("If you keyboard-interrupt, all data will be lost.\n So please be sure to actually quit.")

# ------------------------------------------------------------------------------
def processOneBOWItem(corpus, bow_dict, content_words, STOP_WORDS_LIST):
    sorted_bow = sorted(bow_dict, key=bow_dict.get, reverse=True)
    #print("Testing if this shit is sorted...")
    #print(list(bow_dict)[0])
    #print(list(sorted_bow)[0])
    #first_item = next(iter(sorted_bow)) # first item of sorted bow is the current most frequent
    key = sorted_bow[0]
    value = bow_dict[key]
#for key, value in bow.items():
    while True:
        answer = input("[ " + key + " | " + str(value) + " ] ") #  to stops? [y/n] -- [q to quit]
        if (answer == 'n') or (answer == 's') or (answer == '-'):
            #to_stops.append(key.lower())
            # TODO add: try to lemmatize/decline
            new_forms = prepareForStopwordList(key)
            new_forms.append(key)
            while("" in new_forms):
                new_forms.remove("")
            STOP_WORDS_LIST = STOP_WORDS_LIST + new_forms
            bow_dict.pop(key)
            break
        elif (answer == 'y') or (answer == '') or (answer == 'k') or (answer == 'c') or (answer == '+'):
            # pass value to adding function
            content_words, bow_dict = addItemToContentWordDictIfNotAlreadyIn(key, value, content_words, bow_dict)
            break
        elif answer == 'q':
            informAboutCurrentProgress(bow_dict, corpus)
            #printMostFrequentContentWords(content_words)
            quitBOWProcessing(bow_dict, STOP_WORDS_LIST, content_words)
            quit()
        else:
            continue
    return bow_dict, content_words, STOP_WORDS_LIST

# ------------------------------------------------------------------------------
def getStopwords():
    """
    A function to determine Stopwords given a list from Perseus.
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
def updateStopwordList(new_stopwords):
    """
    This will simply write the current stopwords list to the respective file.
    It will, however, also overwrite the contents of the old file,
    if applicable.
    """
    stop_set = set(new_stopwords)
    new_stopwords_unique = list(stop_set)
    writeListAsOneWordPerLineFile(new_stopwords_unique, "stop_word_list.txt")

# ------------------------------------------------------------------------------
def addToStopWords(STOP_WORDS_LIST, list_of_new_words, logger):
    new_stops = STOP_WORDS_LIST
    declined_forms = (list_of_new_words, "adding declined stopwords", logger)
    new_stops += declined_forms
    updateStopwordList(new_stops)
    # TODO error happens with list of lists..

# ------------------------------------------------------------------------------
def prepareForStopwordList(word):
    logger = ToDosLogger(LOG_FILE)
    normalized = normalizeWord(word) # this will lowercase, so might not work in all cases!
    lemma = getLemmaStrippedOfMarker(lemmatizeWord(normalizeWord(word)))
    #print("[STOPS] This came out of lemmatization: " + lemma)
    decliner = CollatinusDecliner()
    results = []
    try:
        declined_forms = decliner.decline(lemma, flatten=True)
        unique_values = set(declined_forms)
        results = list(unique_values)
        #print("These forms will be added to Stops:")
        #print(results)
    except:
        logger.addToLogger("STOPS", "WARNING", "Lemma couldn't be declined: " + word)
        results.append(word)
    return results

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
    tokens_without_stopwords_match = [w for w in corpus_tokens if not w in stop_words]
    tokens_without_stopwords = [w for w in tokens_without_stopwords_match if not normalizeWord(w) in stop_words]
    return tokens_without_stopwords

# ------------------------------------------------------------------------------
def normalizeWord(word):
    glyphs_removed = normalizeLatinWordsInNonstandardGlyphs(word)
    jv_replaced = jv_replace(glyphs_removed)
    lowercased = jv_replaced.lower()
    return lowercased


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
def updateBagOfWordsFromString(corpus, STOP_WORDS_LIST, content_words):
    """
    Creates a bag of words from a corpus (as string). Using CLTK for Latin.

    Will remove linebreak-hyphens and punctuation as well as stopwords.
    WILL NOT lowercase (!) - so truecasing can be done later, if needed.
    """
    print("\n---\nUpdating the bag of words...")
    normalized = removeHyphensAndPunctuation(corpus)
    #tokens = normalized.split() # this would be the non-Latin/language specific way
    tokens = tokenizeLatinWords(normalized)
    print("\n---\nTokens before stopword-removal: " + str(len(tokens)))
    corpus_without_stopwords = removeStopwordsFromTokens(STOP_WORDS_LIST, tokens)
    print("  * after: " + str(len(corpus_without_stopwords)))
    corpus_without_already_processed_content_words = removeProcessedContentWordsFromBOW(corpus_without_stopwords, content_words)
    print("  * without content words already processed: " + str(len(corpus_without_already_processed_content_words)))
    reduced_corpus = corpus_without_already_processed_content_words
    bow_dict = Counter(corpus_without_already_processed_content_words)

    # remove all items where count is 1 (TODO ggf change later)
    # TODO da nicht lemmatisiert, wird hier evtl durchaus zu viel weggeworfen..
    # d.h. es könnten auch Wortformen eines eh im KOS enthaltenen Wortes mit Glyphs oder so
    # fehlen..
    print("Removing all 1-letter words and all types which only appear once...")
    bow_dict_without_hapaxes = {key:val for key, val in bow_dict.items() if val != 1}
    # also remove all keys that are just one letter
    bow_dict_without_one_letters = {key:val for key, val in bow_dict_without_hapaxes.items() if len(key) != 1}
    print("Bow length after removing hapaxes etc: " + str(len(bow_dict_without_one_letters)))
    return bow_dict_without_one_letters, reduced_corpus

# ------------------------------------------------------------------------------
def updateBagOfWordsFromList(corpus_list, STOP_WORDS_LIST, content_words):
    """
    Creates a bag of words from a corpus (as string). Using CLTK for Latin.

    Will remove linebreak-hyphens and punctuation as well as stopwords.
    WILL NOT lowercase (!) - so truecasing can be done later, if needed.
    """
    print("\n---\nUpdating the bag of words...")

    corpus_without_stopwords = removeStopwordsFromTokens(STOP_WORDS_LIST, corpus_list)
    print("  * after: " + str(len(corpus_without_stopwords)))
    corpus_without_already_processed_content_words = removeProcessedContentWordsFromBOW(corpus_without_stopwords, content_words)
    print("  * without content words already processed: " + str(len(corpus_without_already_processed_content_words)))
    reduced_corpus = corpus_without_already_processed_content_words
    bow_dict = Counter(corpus_without_already_processed_content_words)

    # remove all items where count is 1 (TODO ggf change later)
    # TODO da nicht lemmatisiert, wird hier evtl durchaus zu viel weggeworfen..
    # d.h. es könnten auch Wortformen eines eh im KOS enthaltenen Wortes mit Glyphs oder so
    # fehlen..
    print("Removing all 1-letter words and all types which only appear once...")
    bow_dict_without_hapaxes = {key:val for key, val in bow_dict.items() if val != 1}
    # also remove all keys that are just one letter
    bow_dict_without_one_letters = {key:val for key, val in bow_dict_without_hapaxes.items() if len(key) != 1}
    print("Bow length after removing hapaxes etc: " + str(len(bow_dict_without_one_letters)))
    return bow_dict_without_one_letters, reduced_corpus

# ------------------------------------------------------------------------------
def checkWhichGlyphsArePresent(corpus):
    """
    Will print informative message about which non-standard glyphs are present.
    """
    glyphs_in_general = set(corpus)
    # ſ = s; Æ = AE; æ = ae
    kleinbuchstaben = 'a b c d e f g h i j k l m n o p q r s t u v w x y z '
    grossbuchstaben = 'A B C D E F G H I J K L M N O P Q R S T U V W X Y Z '
    zahlen = '1 2 3 4 5 6 7 8 9 0'
    satzzeichen = '. , : ; \n ? - ( )'
    normale_buchstaben = (kleinbuchstaben + grossbuchstaben + zahlen + satzzeichen).split()

    glyphs_to_be_replaced = [c for c in glyphs_in_general if c not in normale_buchstaben]
    if not glyphs_to_be_replaced:
        print("No glyphs to be replaced")
    else:
        glyphs_string = ' '.join(glyphs_to_be_replaced)
        print("These glyphs have to be replaced: " + glyphs_string)

# ------------------------------------------------------------------------------
def normalizeLatinWordsInNonstandardGlyphs(string):
    """
    Will normalize by first checking which non-standard glyphs are present,
    then replacing them.
    """
    original_string = string
    #checkWhichGlyphsArePresent(string) # only comment in for debug purposes
    # hoffentlich deckt das das meiste ab, was Unicode nicht mag
    string = string.replace('Æ', 'AE')
    string = string.replace('æ', 'ae')
    string = string.replace('ß', 'ss')
    string = string.replace('œ', 'oe')
    string = string.replace('Œ', 'OE')
    string = string.replace('ƒ', 'f')
    string = string.replace('o̅', 'on')
    string = string.replace('ſ', 's')

    unicode_normalized_text = unicodedata.normalize('NFKD',string).encode('ascii','ignore')
    new_string = unicode_normalized_text.decode("utf-8")
    #print("[INFO] Original string: " + original_string + "; unicode-normalized result: " + new_string)
    return new_string



# ------------------------------------------------------------------------------
# CLTK-based Functions
# ------------------------------------------------------------------------------

from cltk.stem.latin.j_v import JVReplacer
from cltk.tokenize.word import WordTokenizer
from cltk.tag import ner
from cltk.lemmatize.latin.backoff import BackoffLatinLemmatizer
from cltk.stem.lemma import LemmaReplacer
lemmatizer = BackoffLatinLemmatizer()
from cltk.stem.latin.declension import CollatinusDecliner

# ------------------------------------------------------------------------------
def jv_replace(text):
    jv_replacer = JVReplacer()
    jv_normalized_text = jv_replacer.replace(text)
    # no lowercasing or Truecasing is done so far!
    # lowercasing probably won't be done but Truecasing needs bow first
    return jv_normalized_text

# ------------------------------------------------------------------------------
# TODO might not be needed anymore...
def declineWord(word, error_type_context,logger):
    error_type = error_type_context + "-declension"

    normalized_string = normalizeLatinWordsInNonstandardGlyphs(word)
    jv_replaced_string = jv_replace(normalized_string)
    lemmatizer = LemmaReplacer('latin')
    try:
        word_list = lemmatizer.lemmatize(word_list)
    except:
        print("Lemmatization error with " + word)
        #logger.addToLogger(error_type, "WARNING", "lemmatization failed: " + word)
        error_count += 1

    decliner = CollatinusDecliner()
    declined_forms = []
    for word in word_list:
        try:
            declined = decliner.decline(word, flatten=True)
            declined_forms = declined_forms + declined
        except:
            logger.addToLogger(error_type, "WARNING", "Lemma couldn't be declined: " + word)
            error_count += 1

    return declined_forms

# ------------------------------------------------------------------------------
# TODO maybe remove
def declineEachWordInList(word_list, error_type_context,logger):
    error_type = error_type_context + "-declension"
    error_count = 0
    total_list_length = len(word_list)

    words_string = ' '.join(word_list)
    normalized_string = normalizeLatinWordsInNonstandardGlyphs(words_string)
    jv_replaced_string = jv_replace(normalized_string)
    word_list = jv_replaced_string.split()
    lemmatizer = LemmaReplacer('latin')
    try:
        word_list = lemmatizer.lemmatize(word_list)
    except:
        print("Lemmatization error with " + word)
        #logger.addToLogger(error_type, "WARNING", "lemmatization failed: " + word)
        error_count += 1


    decliner = CollatinusDecliner()
    declined_forms = []
    for word in word_list:
        try:
            declined = decliner.decline(word, flatten=True)
            declined_forms = declined_forms + declined
        except:
            logger.addToLogger(error_type, "WARNING", "Lemma couldn't be declined: " + word)
            error_count += 1

    print('[' + str(error_count) + ' / ' + str(total_list_length) + '] declension errors')
    return declined_forms

# ------------------------------------------------------------------------------
# https://stackoverflow.com/questions/19859282/check-if-a-string-contains-a-number
def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

# ------------------------------------------------------------------------------
def getLemmaStrippedOfMarker(cltk_lemma):
    if hasNumbers(cltk_lemma) and (len(cltk_lemma) > 1):
        return cltk_lemma[:-1]
    else:
        return cltk_lemma

# ------------------------------------------------------------------------------
def printResultsOfLemmatization(word_list):
    resulting_tuple_list = lemmatizer.lemmatize(word_list)
    # get lemma and form back out of the resulting list of tuples
    for item in resulting_tuple_list:
        form_found = item[0]
        lemma = item[1]
        lemma_stripped_of_number = getLemmaStrippedOfMarker(lemma)
        print("Form found: " + form_found + ";\n\t lemma: " + lemma + ";\n\t without marker: "
          + lemma_stripped_of_number + "\n")
# ------------------------------------------------------------------------------
# interesting find: persName is not found when lowercased!
# lemmatization fails with 'saturno'
# TODO might need jv replacement beforehand...

def lemmatizeAllWordsFromList(word_list):
    """
    This interim function will lemmatize all words from a given list
    and return them as space-separated items in a list
    """
    resulting_tuple_list = lemmatizer.lemmatize(word_list)
    results = []
    for item in resulting_tuple_list:
        form_found = item[0]
        lemma = item[1]
        lemma_stripped_of_number = getLemmaStrippedOfMarker(lemma)
        result = lemma_stripped_of_number + " " + form_found
        results.append(result)
    return results

# ------------------------------------------------------------------------------

def createNERListFromCorpus(string):
    """
    Will use CLTK NER method on a corpus (as string).
    Will perform jv replacement in the process.
    """
    ner_list = []
    jv_replacer = JVReplacer()
    text_str_iu = jv_replacer.replace(string)
    corpus_ner = ner.tag_ner('latin', input_text=text_str_iu)
    for tup in corpus_ner:
        if len(tup) > 1:
            ner_list.append(tup[0])
    NER_unique_values = set(ner_list)
    print('These NER were found in the given corpus:')
    print(NER_unique_values)
    return ner_list

# ------------------------------------------------------------------------------
def tokenizeLatinWords(string):
    print("Tokenizing...")
    word_tokenizer = WordTokenizer('latin')
    text_tokens = word_tokenizer.tokenize(string)
    return text_tokens

# ------------------------------------------------------------------------------
def lemmatizeWord(word):
    lemmatizer = LemmaReplacer('latin')
    result = lemmatizer.lemmatize(word)
    # always returns list
    return result[0]

# ------------------------------------------------------------------------------
def truecase(word, case_counter):
    # this function was adapted from Todd Cook at:
    # https://github.com/todd-cook/ML-You-Can-Use/blob/89b1c04e38e6befd0e7e0515684a96fdc701f995/mlyoucanuse/text_cleaners.py#L285
    """
    Truecase function by Todd Cook (ML You can use Github)

    Will truecase a word based on its usual casing in the bag of words.
    If there aren't any other examples, i.e. we don't have enough data for a decision based on this likelyhood,
    then it will just return the word as is.

    :param word:
    :param case_counter:
    :return:
    """
    lcount = case_counter.get(word.lower(), 0)
    ucount = case_counter.get(word.upper(), 0)
    tcount = case_counter.get(word.title(), 0)
    if lcount == 0 and ucount == 0 and tcount == 0:
        return word  #: we don't have enough information to change the case
    if tcount > ucount and tcount > lcount:
        return word.title()
    if lcount > tcount and lcount > ucount:
        return word.lower()
    if ucount > tcount and ucount > lcount:
        # return word.upper()
        pass
    # TODO vorsicht bei Maier, sonst werden gewisse Titel-Wörter / small caps womöglich alle groß
    return word


# ------------------------------------------------------------------------------
# FINIS
# ------------------------------------------------------------------------------
