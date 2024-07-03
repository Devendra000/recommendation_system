import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from typing import Union

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

products = pd.read_csv('products.csv')

tfidf = TfidfVectorizer(stop_words = 'english')
tfidf_matrix = tfidf.fit_transform(products['category'])
cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)

id = pd.Series(products['id'].values, index=products['name'].values)
name = pd.Series(products['name'].values, index=products['id'].values)
cat = pd.Series(products['category'].values, index=products['id'].values)
level = pd.Series(products['level_of_study'].values, index=products['id'].values)

def sameCategoryProducts(id, cosine_sim = cosine_sim):
    index = id
    sim_score = sorted(enumerate(cosine_sim[index]), key=lambda x:x[1], reverse=True)[0:20]
    return sim_score

tfid = TfidfVectorizer(stop_words = 'english')
tfid_matrix = tfid.fit_transform(products['level_of_study'])
cosine_simf = linear_kernel(tfid_matrix, tfid_matrix)

def sameLevelProducts(id,cosine_simf = cosine_simf):
    index = id
    simL_score = sorted(enumerate(cosine_simf[index]), key=lambda x:x[1], reverse=True)[0:20]
    return simL_score

# # Create separate lists for prioritizing elements with the second element equal to 1.0
# @app.get("/recommend/{product}")
# def getRecommendation(product:str):
#     array1 = sameLevelProducts(product)
#     array2 = sameCategoryProducts(product)
    
#     set1 = set(array1)
#     set2 = set(array2)
    
#     # Identify common elements with second element value 1.0
#     common_elements = {item for item in set1 & set2 if item[1] == 1.0}
    
#     # Separate lists
#     priority_common = []
#     priority_elements = []
#     other_elements = []
#     seen = set()

#     # Function to add unique elements to respective lists
#     def add_unique_elements(array):
#         for item in array:
#             if item[0] not in seen:
#                 if item in common_elements:
#                     priority_common.append(item)
#                 elif item[1] == 1.0:
#                     priority_elements.append(item)
#                 else:
#                     other_elements.append(item)
#                 seen.add(item[0])

#     # Add elements from both arrays
#     add_unique_elements(array1)
#     add_unique_elements(array2)
    
#     # Combine the lists: common elements first, then other prioritized elements, then the rest
#     combined_array = priority_common + priority_elements + other_elements
#     # Extract only the first elements
#     first_elements = [item[0] for item in combined_array if item[0]!=id[product]]
    
#     return name[first_elements]
#     array = [i[0] for i in combined_array]
#     return array

@app.get("/recommendItems/{id}")
def getRecommendationById(id: int):
    product = name[id]
    array1 = sameLevelProducts(id)
    array2 = sameCategoryProducts(id)
    
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
    def add_unique_elements(array, set):
        for item in array:
            if item[0] not in seen:
                if item in common_elements:
                    priority_common.append({"id":item[0], "reason":"Same category and level"})
                elif item[1] == 1.0:
                    if(set == 'level'):
                        priority_elements.append({"id":item[0], "reason":"Same level"})
                    elif(set == 'category'):
                        priority_elements.append({"id":item[0], "reason":"Same category"})
                else:
                    other_elements.append({"id":item[0], "reason":"No reason."})
                seen.add(item[0])
    
    # Add elements from both arrays
    add_unique_elements(array2,'category')
    add_unique_elements(array1,'level')
    
    # Combine the lists: common elements first, then other prioritized elements, then the rest
    combined_array = priority_common + priority_elements + other_elements
    combined_array = combined_array[:21]
    # Extract only the first elements
    recommendations = [item for item in combined_array if item['id']!=id]
    
    return [len(recommendations), recommendations]

recommendation = getRecommendationById(1)
print(recommendation)