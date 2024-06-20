import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

products = pd.read_csv('products.csv')

tfidf = TfidfVectorizer(stop_words = 'english')
tfidf_matrix = tfidf.fit_transform(products['category'])
cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

indices = pd.Series(products.id.values, index=products['name'].drop_duplicates())
cat = pd.Series(products['category'].values, index=products['name'].drop_duplicates())
name = pd.Series(products['name'].values, index=products.index)
level = pd.Series(products['level_of_study'].values, index=products.index)

def sameCategoryProducts(name, cosine_sim = cosine_sim):
  index = indices[name]
  sim_score = sorted(enumerate(cosine_sim[index]), key=lambda x:x[1], reverse=True)[0:20]
  sim_index = [i[0] for i in sim_score]
  sim_index_filtered = [i for i in sim_index if i != index]
  return sim_score

tfid = TfidfVectorizer(stop_words = 'english')
tfid_matrix = tfidf.fit_transform(products['level_of_study'])
cosine_simf = linear_kernel(tfid_matrix, tfid_matrix)

def sameLevelProducts(idx,cosine_simf = cosine_simf):
  index = indices[idx]
  simL_score = sorted(enumerate(cosine_simf[index]), key=lambda x:x[1], reverse=True)[0:20]
  simL_index = [i[0] for i in simL_score]
  simL_index_filtered = [i for i in simL_index if i != index]
  return simL_score

# Create separate lists for prioritizing elements with the second element equal to 1.0
def getRecommendation(product):
  array1 = sameLevelProducts(product)
  array2 = sameCategoryProducts(product)
  
  set1 = set(array1)
  set2 = set(array2)
  
  # Identify common elements with second element value 1.0
  common_elements = {item for item in set1 & set2 if item[1] == 1.0}
  
  # Separate lists
  priority_common = []
  priority_elements = []
  other_elements = []
  seen = set()
  
  # Function to add unique elements to respective lists
  def add_unique_elements(array):
      for item in array:
          if item[0] not in seen:
              if item in common_elements:
                  priority_common.append(item)
              elif item[1] == 1.0:
                  priority_elements.append(item)
              else:
                  other_elements.append(item)
              seen.add(item[0])
  
  # Add elements from both arrays
  add_unique_elements(array1)
  add_unique_elements(array2)
  
  # Combine the lists: common elements first, then other prioritized elements, then the rest
  combined_array = priority_common + priority_elements + other_elements
  
  # Extract only the first elements
  first_elements = [item[0] for item in combined_array]
  
  return name[first_elements]
  array = [i[0] for i in combined_array]
  return array

def getRecommendationById(id):
  product = name[id]
  array1 = sameLevelProducts(product)
  array2 = sameCategoryProducts(product)
  
  set1 = set(array1)
  set2 = set(array2)
  
  # Identify common elements with second element value 1.0
  common_elements = {item for item in set1 & set2 if item[1] == 1.0}
  
  # Separate lists
  priority_common = []
  priority_elements = []
  other_elements = []
  seen = set()
  
  # Function to add unique elements to respective lists
  def add_unique_elements(array):
      for item in array:
          if item[0] not in seen:
              if item in common_elements:
                  priority_common.append(item)
              elif item[1] == 1.0:
                  priority_elements.append(item)
              else:
                  other_elements.append(item)
              seen.add(item[0])
  
  # Add elements from both arrays
  add_unique_elements(array1)
  add_unique_elements(array2)
  
  # Combine the lists: common elements first, then other prioritized elements, then the rest
  combined_array = priority_common + priority_elements + other_elements
  
  # Extract only the first elements
  first_elements = [item[0] for item in combined_array]
  
  return name[first_elements]
  array = [i[0] for i in combined_array]
  return array

recommendation = getRecommendation('Laptop')
print(recommendation)