#!/bin/python

from keras.models import Sequential, model_from_json
from keras.layers.core import Dense, Activation, Dropout
from keras.layers.recurrent import LSTM
from keras.utils.data_utils import get_file

import numpy as np
import random
import sys, os

def sample(a, temperature=1.0):
    # helper function to sample an index from a probability array
    a = np.log(a) / temperature
    a = np.exp(a) / np.sum(np.exp(a))
    return np.argmax(np.random.multinomial(1, a, 1))

def reencode(word):
    word = "|".join([str(x) for x in word])
    return word

def read_training(path):
    text = open(path).read().lower()
    sys.stderr.write("corpus length: " +str(len(text)) + "\n")
    text = text.split()
    newtext = []
    for word in text:
        word = word.split("|")
        word = tuple([float(word[0]), int(word[1]), int(word[2]), float(word[3]), int(word[4]), int(word[5])])
        newtext.append(word)
    return newtext


if __name__ == "__main__":
    path = sys.argv[1]
    filename = path.split("/")[-1].split(".")[0]
    print "Filename:", filename

    text = read_training(path)
    words = set(text)
    sys.stderr.write("total word tokens: " +str(len(text)) + "\n")
    sys.stderr.write("total word types:  " + str(len(words)) + "\n")

    maxlen = 100
    step = 100
    
    sentences,next_words = [],[]
    
    
    #for i in range(0, len(text) - maxlen, step):
    #    sentences.append(text[i: i + maxlen])
    #    next_words.append(text[i + maxlen])
    for i in range(0, len(text) - maxlen, step):
        #sentence = [[x for x in word.split("|")] for word in text[i: i + maxlen]]
        sentence = []
        for word in text[i: i+maxlen]:
            sentence.append(word)
    
        next_word = text[i + maxlen]
        next_words.append(next_word)
        sentences.append(sentence)
    
        
    #sys.stderr.write(str(sentences[:3]) + "...\n")
    sys.stderr.write("nb sequences: " + str(len(sentences)) + "\n")
    sys.stderr.write("Vectorization\n")
    word_indices = dict((w, i) for i,w in enumerate(words))
    indices_words = dict((i, w) for i,w in enumerate(words))
    
    #X = np.zeros((len(sentences), maxlen, len(words)), dtype=np.bool)
    #y = np.zeros((len(sentences), len(words)), dtype=np.bool)

    X = np.zeros((len(sentences), maxlen, 6))
    #y = np.zeros((len(sentences), 6))
    y = np.zeros((len(sentences), len(words)), dtype=np.bool)
    
    #print "X:", str(len(X))+"x"+str(len(X[0]))+"x"+str(len(X[0][0]))
    #print "y:", str(len(y))+"x"+str(len(y[0]))
    
    for i, sentence in enumerate(sentences):
        for t,word in enumerate(sentence):
            X[i, t] = list(word)
        #y[i] = list(next_words[i])
    
        #print next_words[i]
        y[i, word_indices[next_words[i]]] = 1
    
    sys.stderr.write("\n")
    sys.stderr.write("X: " + str(len(X))+"x"+str(len(X[0]))+"x"+str(len(X[0][0])) + "\n")
    sys.stderr.write("y:" + str(len(y))+"x"+str(len(y[0])) + "\n")
    #print X[0]
    #print y[0]

    # for i, sentence in enumerate(sentences):
    #     for t,word in enumerate(sentence):
    #         X[i, t, word_indices[word]] = 1
    #     y[i, word_indices[next_words[i]]] = 1
    
    
    model_arch_file = filename + "_model_arch.json"
    model_weights_file = filename + "_model_weights.h5"
    if os.path.exists(model_arch_file):
        sys.stderr.write("Load Model ...")
        model = model_from_json(open(model_arch_file, "r").read())
        sys.stderr.write("Done.\n")
    else:
        sys.stderr.write("Build Model ...")
        model = Sequential()
        #model.add(LSTM(512, return_sequences=True, input_shape=(maxlen, len(words))))
        model.add(LSTM(512, return_sequences=False, input_shape=(maxlen, 6)))
        model.add(Dropout(0.2))
        
        #model.add(Dense(256, input_shape=(maxlen, 6)))
        #model.add(LSTM(512))
        
        #model.add(LSTM(512, return_sequences=False))
        #model.add(Dropout(0.2))
        
        model.add(Dense(len(words)))
        #model.add(Dense(6))
        model.add(Activation("softmax"))
        #model.add(Activation("relu"))
        
        model.compile(loss="categorical_crossentropy", optimizer="rmsprop")
        #model.compile(loss="mse", optimizer="sgd")
    
        f = open(model_arch_file, "w")
        f.write(model.to_json())
        f.close()
        sys.stderr.write("Done.\n")
    if os.path.exists(model_weights_file):
        sys.stderr.write("Loading Weights.\n")
        model.load_weights(model_weights_file)
    

    MAX_ITER = 100
    for iteration in range(0, MAX_ITER):
        sys.stderr.write("-"*50 + "\n")
        sys.stderr.write("Iteration " + str(iteration) + "\n")
        model.fit(X, y, batch_size=128, nb_epoch=1)
        
        #if iteration % 10 == 0:
        model.save_weights(model_weights_file, overwrite=True)


        """
        #for diversity in [0.2, 0.5, 1.0, 1.2]:
        #for diversity in [1.0]:
        if iteration % 5 == 0 or iteration == MAX_ITER-1:
            diversity = 1.0
            start_index = random.randint(0, len(text) - maxlen - 1)
            f = open(filename+"_iter" + str(iteration+1) + "d:" + str(diversity) + ".output.encoded", "w")
            #f = sys.stdout
        
            #print "----- diversity:", diversity
            generated = ""
            sentence = text[start_index: start_index + maxlen]
            generated += " ".join([reencode(x) for x in sentence])
            #print "----- Generating with seed: ", sentence
            f.write(generated + " ")

            for i in range(400):
                #x = np.zeros((1, maxlen, len(words)))
                x = np.zeros((1, maxlen, 6))
            
                for t,word in enumerate(sentence):
                    #print 0, t, word_indices[word]
                    #x[0, t, word_indices[word]] = 1
                    x[0, t] = word
                #break
            
                preds = model.predict(x, verbose=0)[0]
                next_index = sample(preds, diversity)
                next_word = indices_words[next_index]
                
                generated += reencode(next_word) + " "
                #generated += reencode(preds) + " "
                sentence = sentence[1:] + [next_word]
                f.write(reencode(next_word) + " ")
                f.flush()
        """
        
    model.save_weights(model_weights_file, overwrite=True)
