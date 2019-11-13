# coding: utf-8 -*-
"""
.. module:: get_idlv
   :synopsis: Computing IDLV score - using only dictionaries
   The equation used to compute IDLV value is:
   .. math:: D(P_j) = sum_i=1 to n (e^(-2.3*((i-1/n-i))) * (f_ji / I) )
   where:
    :math:D(P_j) is the lexical availability of word j for a given category
   ## i = position of word j in a given list
   ## f = number of participants who wrote word j at that position in their list
   ## n = the lowest position occupied by word j in any list of that category
   ## I = total number of participants in the task (in this case, we used the frequency of the most common word)
   ## For this implementations of IDLV we normalize (f_ji/I factor) by te proportion of times the word j is written in position i of all times a word can be written in all texts.

.. date_creation:: May 15th, 2019

.. date_last_updated:: Oct 1st, 2019
"""
from __future__ import division
import sys
import os
import math
import fnmatch
import codecs

import logging  ## to use some debug messages


#Funcion que obtiene el nombre del archivo
## Esau's method
def get_file_name(abs_path):
    """Utility function to get files names from a path.

    Parameters
    ----------
    abs_path : string
        absolute path
    """
    path_elements= abs_path.split('/')
    name_elements = path_elements[len(path_elements)-1].split('.')
    return name_elements[0]

##Funcion que permite cargar la lista de archivos a procesar
## Esau's method
def load_files_names(root, patterns ='*', single_level = False, yield_folders = False):
    """Utility function to load files names from a root.

    Parameters
    ----------
    root : string
        absolute path
    patterns: string, optional
        find for a particular pattern. (default is "*")
    single_level : boolean, optional
        (default is False)
    yield_folders : boolean, optional
        (default is False)
    """
    patterns = patterns.split(';')# se puede recibir una lista de extensiones separados por punto y coma
    for path, subdirs, files in os.walk(root):
        if yield_folders:
            files.extend(subdirs)
        files.sort()
        for name in files:
            for pattern in patterns:
                if fnmatch.fnmatch(name, pattern):
                    yield os.path.join(path, name)
                    break
        if single_level:
            break

def write_listtup_tofile(filename, sep, mylist):
    """Utility function to write into file a list of tuples.

    Parameters
    ----------
    filename : string
        output file to be written
    sep: string
        string to use as separator to write down the tuples in filename
    mylist : a dictionary
        with key and values
    """
    string = ""
    for key, value in mylist:
        string += key + sep + str(value) + "\n"
    f = codecs.open(filename, "w", "utf-8")
    f.write(string)
    f.close()

def sortedlist(mydict, topn):
    """Utility function to sort a dictionary according to the value of all keys in it.

    Parameters
    ----------
    mydict : a dictionary
        Contains elements as key:value.
    topn: integer
        determine the top elements to be return after sorting the list

    Returns
    -------
    newlist : a list
        a list containing topn elements
    """
    i=0
    newlist=[]
    max = topn if topn!= None else len(mydict) ## if topn is None, copy the entire list
    for key, value in sorted(mydict.iteritems(), key=lambda(k,v): (v,k),reverse=True):
        if i < max:
            newlist.append((key, value))
            i+=1
        else:
            break
    return newlist



def update_dictionary(my_dict, stats, index, word):
    """Update a dictionary to store all information needed for computing IDVL values

    Given a word and the current position of that word in a given list (or text) update my_dict (a dictionary of vocabulary x indices ); Additionally, this function updates at the same time stats['last_position'] needed when computing the IDLV value; and stats['frequency'] thtat is the total number of times this word appers in this class (set of documents).

    Parameters
    ----------
    my_dict : dictionary of dictionaries
        To be updated each time is called this function, where key = word and value = an array of indices and frecuency of this word in that index
    stats : dictionary of dictionaries
        With 2 main keys: 'last_position' and 'frequency' each of those has a dictionary with key=word and value=last_position or frequency, of this word in the corpus.
    index : integer
        States the current position of this word in a given text.
    word : str
        The word to be added to the dictionary or to be updated

    Returns
    -------
    my_dict
        same input dictionary but updated
    stats
        same input dictionary but updated
    """
    if word not in my_dict:
        ## Words are being added as appering.
        my_dict.setdefault(word, {})
        my_dict[word][index] = 1 ## the first time the frecuency of that word in _index_ is 1
        stats['last_position'].setdefault(word, index)  ## the first dict_last_position_ is this value of _index_
        stats['frequency'].setdefault(word, 1)  ## at the begining the frequency is 1
    else:
        ## the word's already in dictionary, so we need to UPDATE its values
        my_dict[word].setdefault(index,0) ## we added this _index_ if is a new position in the corpus
        my_dict[word][index] += 1  ## increment in one the frecuency of that word in this _index_

        ## update last_position only if index is greater that the current value
        if (stats['last_position'][word] < index):
            stats['last_position'][word] = index
        ## update total frequency
        stats['frequency'][word] += 1

    logging.debug("%s: %s" %(word, my_dict[word]))

    return my_dict, stats

def get_indices(sample, resolution, dict_words_arrayindex, stats):
    """Given a sample text, update the matrix (vocabulary x indices) and the stats dictionary that are useful to compute the IDLV values

    Parameters
    ----------
    sample : str
        Each token to analyze is separated by a single space
    resolution : integer
        The maximum number of slots or indices in this _sample_. If _resolution_ == 1 then absolute positions are consider (a.k.a. the length of _sample_); if _resolution_ > 1 then the _sample_ is divided into _resolution_ parts and each part corresponds to a position (then, total positions for this _sample_ is _resolution_)
    dict_words_arrayindex : dictionary of dictionaries
        Store the entire vocabulary.  It is been updated while samples are read. Where key = word and value = an array of: indices and frecuency of this word in that index.
    stats : dictionary of dictionaries
        With 2 main keys: 'last_position' and 'frequency' each of those has a dictionary with key=word and value=last_position or frequency, of this word in the corpus.
    Returns
    -------
    my_dict
        same input dictionary but updated
    stats
        same input dictionary but updated
    """
    ## eliminate jump line in each lines
    sample = sample.strip("\n")
    ## tokenize the sample input by single space
    words = sample.split(" ")
    logging.debug("len(words)=%d, resolution=%d" % (len(words), resolution))

    jump = 0
    if (resolution > 1):  ## we don't want absolute position
        total_positions = resolution
        jump = math.floor(len(words)/resolution)

    ### if resolution == 1 means we want absolute positions
    ### but resolution > 0 but jump == 0; that means the resolution is bigger than the length of the sample, in this case, we use absolute positions
    if (jump == 0 or resolution == 1):
        total_positions = len(words)
        jump = 1
    #print("[DEBUG]:jump=%d; total_positions=%d" % (jump, total_positions))

    k = 0 ## runs in the vector of words
    for i in range(total_positions):  ## control the maximum numbers of indices requiered according to _resolution_
        for j in range(int(jump)):  ## how many words will have the same index
            w = words[k]  ## read word
            k += 1
            ## update dict_words_arrayindex and stats given this index _i_ and this word _w_
            if (w != ""):
                dict_words_arrayindex, stats = update_dictionary(dict_words_arrayindex, stats, i, w)

    ### if there are other words left in _words_ (this happend when len(words)/resolution is not integer)
    for kk in range(k, len(words)):
        w = words[kk]
        if (w != ""):
            dict_words_arrayindex, stats = update_dictionary(dict_words_arrayindex, stats, i, w)

    return dict_words_arrayindex, stats

def main_idlv(samples, resolution, fout, normalization="max_global", max_features=None, by_instance=False):
    """Main function to compute an idlv list given a set of texts. The main goal of this function is to build the
    IDLV lists of each category from the input files that exist within the input directory

    Parameters
    ----------
    samples : array of strings
        Each row in _samples_ is a single instance. Each item in an instance is separated as a single space (items are called words in this script, but can be n-gramas or others (e.g. "the_cow cow_is is_blak" - in this example, there are 3 items and each one treated as a word)
    resolution : integer
        Specify the maximum number of positions allowed, if == 1 then consider absolute positions of words in the texts; if > 1 then divide the text in that many parts, each part then is considere a position
    fout : str
        A file name (complete path otherwise is written in the current directory) where the list for this _samples_ will be written
    normalization : str, optional
        The type of normalization used when computing IDLV score: can be "max_global",  "max_word" or "num_lists". (default is "max_global")
    max_features : integer , optional
        Specify how many item in the list to be considered (the top max_features with higher score) (default is None meaning keep everything)
    by_instance : bool, optional
        Specify if _samples_ has several samples or only one. If by_instance==False, consider several samples; otherwise is only one sample. (default is False)

    Returns
    -------
    mylist_tup
        An array of tuples [(key, value), (key, value),...] where key is a word in the vocabulary and value its idlv score
    """

    stats = {}
    stats['last_position'] = {}  ## dictionary with dict[word] = the lowest position of that word
    stats['frequency'] = {}  ## dictionary with dict[word] = total frequency of that word in corpus
    stats['idlv'] = {} ## dictionary with dict[word] = idlv value

    dict_words_arrayindex = {} ### dict[word]=dictionary of indices and frequency where this word appears

    if (by_instance==False):
        ## read all samples and build index matrix and last_position
        for sample in samples:
            #sample = sample.strip()
            dict_words_arrayindex, stats = get_indices(sample, resolution, dict_words_arrayindex, stats)
    else:
        ## read only the one sample
        dict_words_arrayindex, stats = get_indices(samples, resolution, dict_words_arrayindex, stats)

    ## now for each word in dict_words_arrayindex compute idlv
    for word in dict_words_arrayindex:
        logging.debug("word = %s "%(word))
        sum = 0.0
        last_index = stats['last_position'][word]
        if normalization=="max_global":
            max_freq = max(stats['frequency'].values())  # The max frequency in all corpus of ANY word --- this is the default
        elif normalization=="max_word": ## normalization=="max_word"
            max_freq = stats['frequency'][word] # The max frequency in all corpus for THIS word
        else: ## normalization=="num_lists"
            max_freq = len(samples) ## uses the num of lists to compute idlv
        for i in range(last_index+1):
            freq_index = dict_words_arrayindex[word][i] if (i in dict_words_arrayindex[word]) else 0
            if freq_index != 0:
                if last_index == 0: # then appers in first position, so e^0=1
                    sum += freq_index/max_freq
                else:
                    sum += math.exp(-2.3*(i/last_index)) * ( freq_index/ max_freq)

                logging.debug("index=%d; freq_index=%d; max_freq=%d; last_index=%d; sum=%f"%(i, freq_index, max_freq, last_index, sum))
        stats['idlv'][word] = sum

    ## sorted lists.
    ## mylist_tup is an array of tuples [(key, value), (key, value),...]
    mylist_tup = sortedlist(stats['idlv'], max_features)

    if (fout!=""):
        #print("[DEBUG]:writing in %s" % fout)
        write_listtup_tofile(fout, "\t", mylist_tup)
    return dict(mylist_tup)

def main(dir_in, dir_out, resolution):
    """Main function for a set of sample's classes. This will call **main_idlv** funtion for each different class.

    Parameters
    ----------
    dir_in : str
        The path that contain N files, each file with one set of samples. For each file in dir_in a idlv_list will be computed
    dir_out : str
        The path where each list will be written
    resolution : integer
        Specify the maximum number of positions allowed, if == 1 then consider absolute positions of words in the texts; if > 1 then divide the text in that many parts, each part then is considere a position. Parameter needed to compute IDLV values.
    """
    #Config how to see the debug mensages
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)  ## set level=logging.DEBUG for more information

    #fetch the number of files contained in the input directory
    files = list(load_files_names(dir_in, '*.txt'))

    ## averything using logging can be ignore, just prints information.
    logging.info("dir_in:%s, res=%d"%(dir_in, resolution))

    logging.debug("reading files: %s" % files)

    #for each file, we compute a IDLV list of terms (one file, one list)
    ## each file has *N* lines, each line is a sample.
    for f in files:
        idlv_file = 'IDLV_list_'+get_file_name(f)+'_'+str(resolution)+'r'+'.idl'
        idlv_file = os.path.join(dir_out, idlv_file)
        samples = open(f,'r')

        main_idlv(samples, resolution, idlv_file)

        samples.close()
    logging.info("Done computing idlv, outputs are in %s\n"%dir_out)
