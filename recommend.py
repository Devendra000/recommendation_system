import pandas as pd
import fastapi as FastApi
import uvicorn
import os
from dotenv import load_dotenv
import pymysql
import sys
import json

from collections import defaultdict

load_dotenv()


from typing import Union

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

# get all product
def getAllProducts():
    connection = pymysql.connect(
                    host=os.getenv('MYSQL_HOST'),
                    user=os.getenv('MYSQL_USER'),
                    password=os.getenv('MYSQL_PASSWORD'),                             
                    db=os.getenv('MYSQL_DATABASE'),
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor ) 

    try:
        with connection.cursor() as cursor:
            sql = "SELECT p.id as id, p.name AS name, c.name AS category, education_level FROM products p JOIN categories c ON p.category_id = c.id;"
            cursor.execute(sql)
            products = cursor.fetchall()
            products = pd.DataFrame(products, columns=['id', 'name', 'category', 'education_level'])
            return products

    finally:
        connection.close()

# get user history
def userHistory(userId: int):
    connection = pymysql.connect(
                    host=os.getenv('MYSQL_HOST'),
                    user=os.getenv('MYSQL_USER'),
                    password=os.getenv('MYSQL_PASSWORD'),                             
                    db=os.getenv('MYSQL_DATABASE'),
                    charset='utf8mb4',
                    cursorclass=pymysql.cursors.DictCursor ) 

    try:
        with connection.cursor() as cursor: 
            # SQL 
            sql = "SELECT clicks FROM users where id = %s" 
            # Execute query.
            cursor.execute(sql,(userId))
            
            userCLicks = cursor.fetchall()
            clicked_products = pd.DataFrame(userCLicks, columns=['clicks'])
            return clicked_products

    finally:
        connection.close()

# Define a hierarchical mapping of levels (adjust as needed)
level_hierarchy = {
    'Bachelors 1st Sem': 1,
    'Bachelors 2nd Sem': 2,
    # Add more levels as per your domain knowledge
}

products = getAllProducts()

# Calculate combined similarity based on category and education_level
def calculate_similarity(clicked_category, clicked_level, product_category, product_level):
    category_similarity = 1.0 if clicked_category == product_category else 0.0
    
    level_similarity = 0.0
    if clicked_level == product_level:
        level_similarity = 1.0
    elif level_hierarchy.get(clicked_level, 0) > level_hierarchy.get(product_level, 0):
        level_similarity = 0.8
    elif level_hierarchy.get(clicked_level, 0) < level_hierarchy.get(product_level, 0):
        level_similarity = 0.6
    
    combined_similarity = 0.5 * category_similarity + 0.5 * level_similarity
    return combined_similarity

# Recommend products based on user's clicked history
def recommend_products_with_user_history(user_clicked_items, n):
# Convert user_clicked_items to integers
    user_clicked_items = list(map(int, user_clicked_items))

    recommended_products = []
    for product_id in user_clicked_items:
        # Index of the clicked product in the products DataFrame
        idx = products.index.get_loc(products[products['id'] == product_id].index[0])

        clicked_name = products.loc[idx, 'name']
        clicked_category = products.loc[idx, 'category']
        clicked_level = products.loc[idx, 'education_level']

        # Calculate similarity scores with all products based on category and education_level
        similarity_scores = []
        for i in range(len(products)):
            if products.loc[i, 'id'] != product_id:
                
                product_category = products.loc[i, 'category']
                product_level = products.loc[i, 'education_level']
                similarity_score = calculate_similarity(clicked_category, clicked_level, product_category, product_level)
                similarity_scores.append((i, similarity_score))
        
        # Sort by similarity score (descending)
        similarity_scores_sorted = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
        
        # Extract top n recommendations
        top_n_recommendations = []
        for i, score in similarity_scores_sorted[:n]:
            top_n_recommendations.append({
                'id': products.loc[i, 'id'],
                'name': products.loc[i, 'name'],
                'similarity_score': score,
            })
        
        recommended_products.append({
            'clicked_product': clicked_name,
            'recommended_products': top_n_recommendations
        })

    return recommended_products


# Recommend products for clicked product
def recommend_products_with_productId(product_id, n):
    print('in recommend_products_with_productId')
    recommended_products = []
    
    print(products)
    # Index of the clicked product in the products DataFrame
    idx = products.index.get_loc(products[products['id'] == product_id].index[0])
    clicked_name = products.loc[idx, 'name']
    clicked_category = products.loc[idx, 'category']
    clicked_level = products.loc[idx, 'education_level']
    
    # Calculate similarity scores with all products based on category and education_level
    similarity_scores = []
    for i in range(len(products)):
        print ("product id", products.loc[i, 'id'])
        if products.loc[i, 'id'] != product_id:
            product_category = products.loc[i, 'category']
            product_level = products.loc[i, 'education_level']
            similarity_score = calculate_similarity(clicked_category, clicked_level, product_category, product_level)
            print('prod',similarity_score)
            similarity_scores.append((i, similarity_score))
    
        print (similarity_scores)
        # Sort by similarity score (descending)
        similarity_scores_sorted = sorted(similarity_scores, key=lambda x: x[1], reverse=True)
        
        # Extract top n recommendations
        top_n_recommendations = []
        for i, score in similarity_scores_sorted[:n]:
            top_n_recommendations.append({
                'id': products.loc[i, 'id'],
                'name': products.loc[i, 'name'],
                'similarity_score': score,
            })
        
        recommended_products.append({
            'clicked_product': clicked_name,
            'recommended_products': top_n_recommendations
        })
        
    return recommended_products
    
# Recommend products based on user's clicked history
@app.get("/recommendItemsForUser/{userId}/{n}")
def getRecommendationForUser(userId: int, n: int):
    # return id
    clicked_products = userHistory(userId)
    recommendations = recommend_products_with_user_history(json.loads(clicked_products['clicks'][0]), n)
    recommendation = []
    for rec in recommendations:
        clicked = rec['clicked_product']
        for product in enumerate(rec['recommended_products']):
            recommendation.append({'id':product[1]['id'].item(), 'name':product[1]['name'], 'reason':f'You clicked on {clicked}', 'similarity_score':product[1]['similarity_score']})
            
    for rec in recommendation:
        rec['id'] = int(rec['id'])

    # Sort recommendations based on similarity_score in descending order
    sorted_recommendations = sorted(recommendation, key=lambda x: x['similarity_score'], reverse=True)

    max_similarity = {}
    for rec in sorted_recommendations:
        id_ = rec['id']
        score = rec['similarity_score']
        if id_ not in max_similarity or score > max_similarity[id_]['similarity_score']:
            max_similarity[id_] = rec

    filtered_recommendations = list(max_similarity.values())

    return filtered_recommendations[:n]

# Recommend products for clicked product
@app.get("/recommendItemsByProductId/{product_id}/{n}")
def getRecommendation(product_id: int, n: int):
    recommendations = recommend_products_with_productId(product_id, n)
    
    recommendation = []
    for rec in recommendations:
        clicked = rec['clicked_product']
        for product in enumerate(rec['recommended_products']):
            recommendation.append({'id':product[1]['id'].item(), 'name':product[1]['name'], 'reason':f'You clicked on {clicked}', 'similarity_score':product[1]['similarity_score']})
            
    for rec in recommendation:
        rec['id'] = int(rec['id'])

    # Sort recommendations based on similarity_score in descending order
    sorted_recommendations = sorted(recommendation, key=lambda x: x['similarity_score'], reverse=True)
    
    max_similarity = {}
    for rec in sorted_recommendations:
        id_ = rec['id']
        score = rec['similarity_score']
        if id_ not in max_similarity or score > max_similarity[id_]['similarity_score']:
            max_similarity[id_] = rec

    # Step 2: Extract values from the dictionary to get filtered recommendations
    filtered_recommendations = list(max_similarity.values())

    # Step 3: Print or use filtered_recommendations
    print(filtered_recommendations)
    return filtered_recommendations[:n]

