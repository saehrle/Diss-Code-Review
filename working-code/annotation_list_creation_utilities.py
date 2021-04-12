
# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

from collections import Counter # for bow creation

import regex as re # sudo -H python3 -m pip install regex
from tqdm import tqdm # to display a progress bar

from nltk.probability import FreqDist

from ToDosLogger import *
from helper_functions import *
from cltk_based_text_processing import lemmatizeWord, getLemmaStrippedOfMarker, tokenizeLatinWords
from cltk.stem.latin.declension import CollatinusDecliner

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
def informAboutCurrentProgress(bow_dict, corpus):
    original_corpus_length_unique = getCorpusSize(corpus)
    current_bow_size = len(bow_dict)
    frequency_distribution = FreqDist(corpus.split())
    frequency_distribution.plot(40,title='Frequency distribution for 40 most common tokens')
    print("\nCorpus has [" + str(original_corpus_length_unique) + \
      "] unique values, of which [" + str(current_bow_size) + "] are still in the BOW to be processed.")
    showProgressBar(original_corpus_length_unique, current_bow_size)

# ------------------------------------------------------------------------------
def getContentWordsDict():
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
def removeProcessedContentWordsFromBOW(tokens, content_words):
    bow_dict_types_list = [value[1] for key, value in content_words.items()]
    bow_types = []
    for types_list in bow_dict_types_list:
        bow_types += types_list
    #print("-----------------> These strings are in the bow removal list..")
    #print(bow_types)
    bow_types = normalizeList(bow_types)

    #print("\n---\nTokens before removal of content words: " + str(len(tokens)))
    #TODO code below is not actually worth it, only removed about 40 more items (in close to 3mio tokens)
    # bzw iwas kann da net ganz stimmen?
    corpus_tokens = tqdm(tokens)
    corpus_tokens.set_description("Removal of already processed content words")
    tokens_without_normalized_content_words = [w for w in corpus_tokens if not normalizeWord(w) in bow_types]


    corp_toks = tqdm(tokens_without_normalized_content_words)
    corp_toks.set_description("Removal of already processed content words (normalized)")
    tokens_without_content_words = [w for w in corp_toks if not w in bow_types]
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
        #   bow_dict.pop(original_word)
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
    #normalized = normalizeWord(word) # this will lowercase, so might not work in all cases!
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
    #print("\n---\nTokens before stopword-removal: " + str(len(tokens)))
    corpus_without_stopwords = removeStopwordsFromTokens(STOP_WORDS_LIST, tokens)
    #print("  * after: " + str(len(corpus_without_stopwords)))
    corpus_without_already_processed_content_words = removeProcessedContentWordsFromBOW(corpus_without_stopwords, content_words)
    #print("  * without content words already processed: " + str(len(corpus_without_already_processed_content_words)))
    reduced_corpus = corpus_without_already_processed_content_words
    reduced_corpus = cleanCorpus(reduced_corpus)
    bow_dict = Counter(corpus_without_already_processed_content_words)

    # remove all items where count is 1 (TODO ggf change later)
    # TODO da nicht lemmatisiert, wird hier evtl durchaus zu viel weggeworfen..
    # d.h. es könnten auch Wortformen eines eh im KOS enthaltenen Wortes mit Glyphs oder so
    # fehlen..
    #print("Removing all 1-letter words and all types which only appear once...")
    dict_items = tqdm(bow_dict.items())
    dict_items.set_description("Removing hapaxes")
    bow_dict_without_hapaxes = {key:val for key, val in dict_items if val != 1}
    # also remove all keys that are just one letter
    bow_dict_without_one_letters = {key:val for key, val in bow_dict_without_hapaxes.items() if len(key) != 1}
    #print("Bow length after removing hapaxes etc: " + str(len(bow_dict_without_one_letters)))
    #print("With stopswords " + str(len(tokens)) + " tokens, " + str(len(reduced_corpus)) + " without.")
    print("After removing 1-letter words and hapaxes: " + str(len(bow_dict_without_one_letters)) + " left.")
    return bow_dict_without_one_letters, reduced_corpus

# ------------------------------------------------------------------------------
# ggf delete later
def updateBagOfWordsFromDictFile(corpus, STOP_WORDS_LIST, content_words):
    """
    Creates a bag of words from a corpus (as string). Using CLTK for Latin.

    Will remove linebreak-hyphens and punctuation as well as stopwords.
    WILL NOT lowercase (!) - so truecasing can be done later, if needed.
    """
    print("\n---\nUpdating the bag of words...")
    #print("\n---\nTokens before stopword-removal: " + str(len(tokens)))
    corpus_without_stopwords = removeStopwordsFromTokens(STOP_WORDS_LIST, corpus)
    #print("  * after: " + str(len(corpus_without_stopwords)))
    corpus_without_already_processed_content_words = removeProcessedContentWordsFromBOW(corpus_without_stopwords, content_words)
    #print("  * without content words already processed: " + str(len(corpus_without_already_processed_content_words)))
    reduced_corpus = corpus_without_already_processed_content_words
    reduced_corpus = cleanCorpus(reduced_corpus)
    bow_dict = Counter(corpus_without_already_processed_content_words)

    # remove all items where count is 1 (TODO ggf change later)
    # TODO da nicht lemmatisiert, wird hier evtl durchaus zu viel weggeworfen..
    # d.h. es könnten auch Wortformen eines eh im KOS enthaltenen Wortes mit Glyphs oder so
    # fehlen..
    #print("Removing all 1-letter words and all types which only appear once...")

    bow_dict_without_hapaxes = {key:val for key, val in bow_dict.items() if val != 1}
    # also remove all keys that are just one letter
    #bow_dict_without_one_letters = {key:val for key, val in bow_dict_without_hapaxes.items() if len(key) != 1}
    #print("Bow length after removing hapaxes etc: " + str(len(bow_dict_without_one_letters)))
    #print("With stopswords " + str(len(tokens)) + " tokens, " + str(len(reduced_corpus)) + " without.")
    print("After removing 1-letter words and hapaxes: " + str(len(bow_dict_without_hapaxes)) + " left.")
    return bow_dict_without_hapaxes, reduced_corpus

# ------------------------------------------------------------------------------
def updateBagOfWordsFromList(corpus_list, STOP_WORDS_LIST, content_words):
    """
    Creates a bag of words from a corpus (as string). Using CLTK for Latin.

    Will remove linebreak-hyphens and punctuation as well as stopwords.
    WILL NOT lowercase (!) - so truecasing can be done later, if needed.
    """
    print("\n---\nUpdating the bag of words...")

    #TODO ist die Frage, ob man das alles braucht bzw. ob man überhaupt den BOW neu machen müsste?
    # wird bei größere Datenmenge langsam ziemlich beschwerlich
    # die Maßnahme sollte es ja eig einfacher machen, nicht komplizierter

    corpus_without_stopwords = removeStopwordsFromTokens(STOP_WORDS_LIST, corpus_list)
    #print("  * after: " + str(len(corpus_without_stopwords)))
    corpus_without_already_processed_content_words = removeProcessedContentWordsFromBOW(corpus_without_stopwords, content_words)
    #print("  * without content words already processed: " + str(len(corpus_without_already_processed_content_words)))
    reduced_corpus = corpus_without_already_processed_content_words
    #reduced_corpus = cleanCorpus(corpus_list)
    reduced_corpus = cleanCorpus(corpus_without_already_processed_content_words)
    bow_dict = Counter(reduced_corpus)

    # remove all items where count is 1 (TODO ggf change later)
    # TODO da nicht lemmatisiert, wird hier evtl durchaus zu viel weggeworfen..
    # d.h. es könnten auch Wortformen eines eh im KOS enthaltenen Wortes mit Glyphs oder so
    # fehlen..
    #TODO eig braucht es das Folgende bei From list nicht mehr, weil eig sollte das hier eh nicht mehr drin sein..
    #print("Removing all 1-letter words and all types which only appear once...")

    #bow_dict_without_hapaxes = {key:val for key, val in bow_dict.items() if val != 1}

    # also remove all keys that are just one letter
    #bow_dict_without_one_letters = {key:val for key, val in bow_dict_without_hapaxes.items() if len(key) != 1}
    #print("Bow length after removing hapaxes etc: " + str(len(bow_dict_without_one_letters)))
    return bow_dict, reduced_corpus



# ------------------------------------------------------------------------------
# FINIS
# ------------------------------------------------------------------------------
