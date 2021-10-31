import tensorflow.keras
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Dense, Conv2D, MaxPool2D, Activation, BatchNormalization, Flatten, InputLayer, Input, GlobalAveragePooling2D, Dropout
from tensorflow.keras.optimizers import SGD
from tensorflow.keras.models import load_model
import os
import cv2
import numpy as np
import matplotlib.pyplot as plt
import pickle
from tensorflow.keras.preprocessing import image
import random
from sklearn.utils import shuffle, class_weight
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, accuracy_score, average_precision_score, confusion_matrix, precision_recall_curve, auc
from tensorflow.keras import backend as K
from tensorflow.keras.callbacks import ModelCheckpoint, TensorBoard
from itertools import combinations
from sklearn.metrics import classification_report
from keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.utils import to_categorical

pickle_in = open("/home/fproenca/Tese/Data/HDA/x_total.pickle","rb")
x = pickle.load(pickle_in)

pickle_in = open("/home/fproenca/Tese/Data/HDA/labels_total.pickle","rb")
labels = pickle.load(pickle_in)

def get_mobile_net(x):

	model = load_model('/home/fproenca/Tese/Results/HDA/MobileNet_Class_224.h5')
	new_model = Model(model.input, model.layers[-3].output)
	
	new_model.summary()
	
	feature_vectors = []
	i=0
	for xi in x:
	  feature_vectors.append(new_model.predict(np.expand_dims(xi, axis=0)))
	  i+=1
	
	for j in range(len(feature_vectors)):
		feature_vectors[j] = feature_vectors[j][0]
	
	feature_vectors = np.array(feature_vectors)

	return feature_vectors

#Obtain feature vectors
feat_vect = get_mobile_net(x)
#Save them
pickle_out = open("/home/fproenca/Tese/Data/CUHK01/feat_vect.pickle","wb")
pickle.dump(feat_vect, pickle_out)
pickle_out.close()


def AP_calculation(rank_vector,number_matches):
  prev = 1/number_matches
  sum = 0
  cnt = 0
  for idx, a in enumerate(rank_vector):
    if a == 0:
      continue
    else:
      cnt += 1
      sum = sum + cnt/(idx+1)
  AP = prev * sum
  return AP
  
def map_calculate(ap_vector, query_number):
  prev = 1 / query_number
  af = np.sum(ap_vector)

  mAP = prev * af
  return mAP

  #Calculate mAP
def calculate_map(sum_ranks, n):
  sum = 0
  for i in range(len(sum_ranks)):
    sum += sum_ranks[i]/(i+1)
  map = (1/n)*sum
  print(map)

  return map

def euclidean_distance_(querys, gallery, topk):
    aux = 0
    valid_queries = 0
    all_rank = []
    all_rank_map = []
    sum_rank = np.zeros(topk)
    for query in querys:
        aux += 1
        print(aux)
        q_id = query[0]
        q_feature = query[1]
        # Calculate the distances for each query
        distmat = []
        for label, feature in gallery:
            dist = siamese.predict([np.expand_dims(q_feature, axis=0), np.expand_dims(feature, axis=0)])
            distmat.append([dist, label])
        # Sort the results for each query
        distmat.sort(reverse= True)
        # Find matches
        matches = np.zeros(len(distmat))
        # Zero if no match 1 if match
        for i in range(0, len(distmat)):
            if distmat[i][1] == q_id:
                # Match found
                matches[i] = 1
        rank = np.zeros(topk)
        rank_map = np.zeros(topk)
        for i in range(0, topk):
            if matches[i] == 1:
                rank_map[i] = 1
        for i in range(0, topk):
            if matches[i] == 1:
                rank[i] = 1
                # If 1 is found then break as you dont need to look further path k
                break
        valid_queries +=1
        all_rank.append(rank)
        all_rank_map.append(rank_map)
    for i in all_rank_map:
        print ("-->" + str(i[0]) + " " + str(i[1]) + " " + str(i[2]) + " " + str(i[3]) + " " + str(i[4]) + " " + str(i[5]) + " " + str(i[6]) + " " + str(i[7]) + " " + str(i[8]) + " " + str(i[9]) + " " + str(i[10]) + " " + str(i[11]) + " " + str(i[12]) + " " + str(i[13]) + " " + str(i[14]) + " " + str(i[15]) + " "  )
    print("............................................")
    ## CMC curve - Rank results ##
    sum_all_ranks = np.zeros(len(all_rank[0]))
    for i in range(0,len(all_rank)):
        my_array = all_rank[i]
        for g in range(0, len(my_array)):
            sum_all_ranks[g] = sum_all_ranks[g] + my_array[g]
    sum_all_ranks = np.array(sum_all_ranks)
    print("NPSAR", sum_all_ranks)
    cmc_restuls = np.cumsum(sum_all_ranks) / 100
    print(cmc_restuls)
    ##  mAP calculation ##
    AP = np.zeros(len(all_rank_map))
    for i in range(0,len(all_rank_map)):
        my_array = all_rank_map[i]
        # Change if not single gallery shot and not 100 queries#
        AP[i] = AP_calculation(my_array,2)
    map = map_calculate(AP, 100)
    

    return cmc_restuls, sum_all_ranks, map


#-> Create Gallery and Query lists for test
query_list = []
gallery_list = []
x_classes = []
labels_classes = []
person_list = np.zeros(67)
leng = 3
#-> Save in each x_classes and in labels_classes each feature vector and label
for j in range(1, 67):
  aux_x = []
  aux_labels = []
  for i in range(len(labels)):
    if labels[i] == j:
      aux_x.append(x[i])
      aux_labels.append(labels[i])
  x_classes.append(aux_x)
  labels_classes.append(aux_labels)
#print(labels_classes) #Print all labels 
#-> Create the gallery list
for i in range(33,66):
  b = (len(labels_classes[i])-1)
  if b+1 < leng:
    print("problem ---> " + str(b+1) + "  " + str(i))
    print(i)
    gallery_list.append([labels_classes[i][1], x_classes[i][1]])
    person_list[i+1] = 1
  else:
    random.seed(i+9)
    rand = random.sample(range(1, b+1), leng-1)
    for s in range(0,leng-1):
      gallery_list.append([labels_classes[i][rand[s]], x_classes[i][rand[s]]])
      person_list[i+1] = leng-1
# Choose 100 random test ids
random.seed(0)
randomlist = random.sample(range( 33,66), 33)
# Build the query list
for i in randomlist:
    query_list.append([labels_classes[i][0], x_classes[i][0]])
aux = 0
while len(gallery_list) < 1999: 
  aux += 1   
  for i in range(0,33):
    b = (len(labels_classes[i])-1)
    random.seed(i + aux)
    rand = random.randint(0,b)
    gallery_list.append([labels_classes[i][rand], x_classes[i][rand]])



cmc_re, sum_ranks, map = euclidean_distance_(query_list, gallery_list, len(gallery_list))

print("2048 -> Rank1: " + str(cmc_re[0]) + " Rank_5: " + str(cmc_re[4]) + " Rank_10: " + str(cmc_re[9]) + " Rank_20: " + str(cmc_re[19]))
print(cmc_re[:50])
print(map)
map_2048 = calculate_map(sum_ranks, len(query_list))
print(map_2048)
