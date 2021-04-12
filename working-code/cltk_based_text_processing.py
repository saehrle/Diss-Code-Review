# ------------------------------------------------------------------------------
# Imports
# ------------------------------------------------------------------------------

import cltk # for processing Natural Language Processing of Latin

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

import unicodedata # for removing ligatures from data in pre-processing

# ------------------------------------------------------------------------------
def jv_replace(text):
    """
    Will perform CLTK-based jv_replacement.
    """
    jv_replacer = JVReplacer()
    jv_normalized_text = jv_replacer.replace(text)
    # no lowercasing or Truecasing is done so far!
    # lowercasing probably won't be done but Truecasing needs bow first
    return jv_normalized_text

# ------------------------------------------------------------------------------
# https://stackoverflow.com/questions/19859282/check-if-a-string-contains-a-number
def hasNumbers(inputString):
    """
    Checks if inputString has numbers in it and returns true/false.
    """
    return any(char.isdigit() for char in inputString)

# ------------------------------------------------------------------------------
def getLemmaStrippedOfMarker(cltk_lemma):
    """
    Will strip a string off its last char if the string contains numbers.
    This is meant to remove numbering on lemmata outputted by CLTK
    which result in failing declension if passed on as is.
    """
    if hasNumbers(cltk_lemma) and (len(cltk_lemma) > 1):
        return cltk_lemma[:-1]
    else:
        return cltk_lemma

# ------------------------------------------------------------------------------
def printResultsOfLemmatization(word_list):
    """
    A debug/helper function to check the result of lemmatization and getLemmaStrippedOfMarker.
    """
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
    """
    Uses the CLTK Latin Tokenizer for Latin-specific tokenization.
    Accepts string, returns list of tokens.
    """
    print("Tokenizing...")
    word_tokenizer = WordTokenizer('latin')
    text_tokens = word_tokenizer.tokenize(string)
    return text_tokens

# ------------------------------------------------------------------------------
def lemmatizeWord(word):
    """
    CLTK-based lemmatization function to lemmatize a single word.

    Since CLTK lemmatization always returns a list, it will only return the
    first element of that list. If you want the whole list or lemmatize more
    than one word, use lemmatizeAllWordsFromList.
    This function has no error checking in form of try-catch or anything.
    It's possible that lemmatization fails and thus, the returned string is empty.
    """
    lemmatizer = LemmaReplacer('latin')
    result = lemmatizer.lemmatize(word)
    # always returns list
    return result[0]


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



# ------------------------------------------------------------------------------
# TODO might not be needed anymore...
def declineWord(word, error_type_context,logger):
    """
    A declension function which might not be needed anymore.
    """
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
    """
    A declension function which might not be needed anymore.
    """
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
