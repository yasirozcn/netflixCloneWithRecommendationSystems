from flask import Flask, request, jsonify
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
import mysql.connector
import requests
import random
from hashlib import sha256
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Origin', '*')  # Allow requests from any origin
    return response

def item_based_recommendation(movie_title, min_ratings=40, top_n=10):
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '54zs106ve449',
        'database': 'recom'
    }

    conn = mysql.connector.connect(**db_config)

    data_query = "SELECT * FROM ratings_small"
    data = pd.read_sql_query(data_query, conn)

    conn.close()

    selected_columns = pd.read_csv(r"/Users/ahmetyasirozcan/Desktop/Homeworks/recommendation_systems/archive/selected_movies.csv")

    selected_columns = selected_columns.rename(columns={"id": "movieId"})
    selected_columns = selected_columns[['movieId', 'original_title']]
    selected_columns['movieId'] = pd.to_numeric(selected_columns['movieId'], errors='coerce', downcast='integer')
    selected_columns = selected_columns.dropna(subset=['movieId']).astype({'movieId': 'int'})
    selected_columns = selected_columns.sort_values(by='movieId')
    merged_data = pd.merge(data, selected_columns, on='movieId', how='inner')
    merged_data.drop('timestamp', axis=1, inplace=True)

    table = merged_data.pivot_table(index="userId", columns="original_title", values="rating")

    recommend = table[movie_title]

    correlation = table.corrwith(recommend)

    correlation_dataframe = pd.DataFrame(correlation, columns=["Correlation"])

    correlation_dataframe.dropna(inplace=True)

    correlation_dataframe = correlation_dataframe.sort_values("Correlation", ascending=False)

    ratings = pd.DataFrame(merged_data.groupby("original_title")["rating"].mean())
    ratings["number_of_ratings"] = merged_data.groupby("original_title")["rating"].count()

    ratings.sort_values(by="number_of_ratings", ascending=False, inplace=True)

    correlation_dataframe = correlation_dataframe.join(ratings["number_of_ratings"])

    final_recommendation = correlation_dataframe[correlation_dataframe["number_of_ratings"] > min_ratings] \
        .sort_values("Correlation", ascending=False)[:top_n]
    
    final_recommendation = final_recommendation.reset_index()
    final_recommendation = pd.merge(final_recommendation, selected_columns, on='original_title', how='left')
    final_recommendation = final_recommendation.rename(columns={"movieId": "movieId", "original_title": "movieName"})

    return final_recommendation[['movieId', 'movieName', 'Correlation', 'number_of_ratings']]

def recommend_movies_for_user(user_id, n=10, user_similarity_threshold=0.2, m=10):
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '54zs106ve449',
        'database': 'recom'
    }

    conn = mysql.connector.connect(**db_config)

    data_query = "SELECT * FROM ratings_small"
    ratings = pd.read_sql_query(data_query, conn)

    conn.close()

    selected_columns = pd.read_csv(r"/Users/ahmetyasirozcan/Desktop/Homeworks/recommendation_systems/archive/selected_movies.csv")
    
    selected_columns = selected_columns.rename(columns={"id": "movieId"})
    movie_names = selected_columns.copy()
    movie_names['movieId'] = pd.to_numeric(movie_names['movieId'], errors='coerce', downcast='integer')
    movie_names = movie_names.dropna(subset=['movieId']).astype({'movieId': 'int'})
    movie_names = movie_names.sort_values(by='movieId')
    
    merged_data = pd.merge(ratings, movie_names, on='movieId', how='inner')
    merged_data.drop('timestamp', axis=1, inplace=True)
    
    agg_ratings = merged_data.groupby('original_title').agg(mean_rating=('rating', 'mean'),
                                                            number_of_ratings=('rating', 'count')).reset_index()

    ratings_50 = agg_ratings[agg_ratings['number_of_ratings'] > 50]

    matrix = merged_data.pivot_table(index='userId', columns='original_title', values='rating')

    matrix_norm = matrix.subtract(matrix.mean(axis=1), axis='rows')
    scaler = MinMaxScaler()
    matrix_norm_scaled = pd.DataFrame(scaler.fit_transform(matrix_norm), index=matrix_norm.index, columns=matrix_norm.columns)

    user_similarity_cosine = cosine_similarity(matrix_norm_scaled.fillna(0))
    user_similarity_cosine_df = pd.DataFrame(user_similarity_cosine, index=matrix_norm_scaled.index, columns=matrix_norm_scaled.index)

    scaler = MinMaxScaler()
    user_similarity_normalized = pd.DataFrame(scaler.fit_transform(user_similarity_cosine_df), index=user_similarity_cosine_df.index, columns=user_similarity_cosine_df.columns)

    user_similarity_normalized.drop(index=user_id, inplace=True)

    similar_users = user_similarity_normalized[user_similarity_normalized[user_id] > user_similarity_threshold][user_id].sort_values(
        ascending=False)[:n]

    user_id_watched = matrix_norm_scaled[matrix_norm_scaled.index == user_id].dropna(axis=1, how='all')

    similar_user_movies = matrix_norm_scaled[matrix_norm_scaled.index.isin(similar_users.index)].dropna(axis=1, how='all')

    similar_user_movies.drop(user_id_watched.columns, axis=1, inplace=True, errors='ignore')

    item_score = {}

    for i in similar_user_movies.columns:
        movie_rating = similar_user_movies[i]
        total = 0
        count = 0
        for u in similar_users.index:
            if pd.notna(movie_rating[u]):
                score = similar_users[u] * movie_rating[u]
                total += score
                count += 1
        if count > 0:
            item_score[i] = total / count

    item_score_df = pd.DataFrame(item_score.items(), columns=['original_title', 'movie_score'])

    ranked_item_score = item_score_df.sort_values(by='movie_score', ascending=False)

    recommended_movies = ranked_item_score.head(m)

    recommended_movies_with_id = pd.merge(recommended_movies, merged_data[['original_title', 'movieId']], on='original_title', how='inner')
    recommended_movies_with_id.drop_duplicates(inplace=True)
    
    return recommended_movies_with_id[['movieId', 'original_title', 'movie_score']]

def get_movie_details(movie_id):
    api_key = '6133d9a22c9c2a11c2cbd28843448ad3'
    url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US'
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            movie_data = response.json()
            
            movie_details = {
                'title': movie_data['title'],
                'overview': movie_data['overview'],
                'release_date': movie_data['release_date'],
                'poster_path': movie_data['poster_path']  # İsteğe bağlı: film afişi
            }
            
            return movie_details
        else:
            print(f"TMDB API request failed with status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

    try:
        db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '54zs106ve449',
            'database': 'recom'
        }

        # Veritabanı bağlantısı
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Her film için kullanıcı-film ilişkisini veritabanına ekle
        for movie_id in movie_ids:
            # SQL sorgusu
            sql = "INSERT INTO ratings_small (userId, movieId, rating) VALUES (%s, %s, %s)"
            # Parametreler
            val = (user_id, movie_id, 5)  # Kullanıcının tüm favori filmlerine 5 puan veriyoruz
            # Sorguyu çalıştırma
            cursor.execute(sql, val)

        # Değişiklikleri kaydetme ve bağlantıyı kapatma
        conn.commit()
        conn.close()

        return {'success': True, 'message': 'Favorite movies added successfully.'}

    except Exception as e:
        return {'success': False, 'error': str(e)}

def generate_unique_id(string):
    # Verilen string'in SHA-256 hash'ini al
    hashed = sha256(string.encode()).hexdigest()
    # İlk 8 karakteri alarak benzersiz bir tamsayı oluştur
    unique_id = int(hashed[:8], 16)
    return unique_id


@app.route('/movies/details', methods=['GET'])
def get_filtered_movie_details():
    try:
        # Database connection and ratings retrieval
        db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '54zs106ve449',
            'database': 'recom'
        }

        conn = mysql.connector.connect(**db_config)
        data_query = "SELECT movieId FROM ratings_small"
        ratings_data = pd.read_sql_query(data_query, conn)
        conn.close()

        # Load and convert selected movies' Id to int
        selected_movies = pd.read_csv("/Users/ahmetyasirozcan/Desktop/Homeworks/recommendation_systems/archive/selected_movies.csv")
        selected_movies['id'] = pd.to_numeric(selected_movies['id'], errors='coerce', downcast='integer')


        # Find common Id's and filter
        filtered_movies = selected_movies[selected_movies['id'].isin(ratings_data['movieId'])]

        # Retrieve details for the first 10 filtered movies
        movie_ids = filtered_movies['id'].head(10).tolist()
        movie_details_list = []
        for movie_id in movie_ids:
            movie_details = get_movie_details(movie_id)
            if movie_details:
                movie_details_list.append(movie_details)

        return jsonify(movie_details_list)

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': 'An error occurred while processing your request.'}), 500
    
@app.route('/ib', methods=['GET'])
def item_based_recommend():
    movie_title = request.args.get('movie_title')

    recommendations = item_based_recommendation(movie_title)

    response = recommendations.to_json(orient='records')

    return response

@app.route('/ub', methods=['GET'])
def user_based_recommend():
    user_id = request.args.get('user_id')

    recommendations = recommend_movies_for_user(user_id)

    response = recommendations.to_json(orient='records')

    return response

@app.route('/new', methods=['GET'])
def get_random_movies():
    try:
        db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '54zs106ve449',
            'database': 'recom'
        }

        conn = mysql.connector.connect(**db_config)
        data_query = "SELECT movieId FROM ratings_small"
        ratings_data = pd.read_sql_query(data_query, conn)
        conn.close()

        selected_movies = pd.read_csv("/Users/ahmetyasirozcan/Desktop/Homeworks/recommendation_systems/archive/selected_movies.csv")
        selected_movies['id'] = pd.to_numeric(selected_movies['id'], errors='coerce', downcast='integer')

        # Find common Id's and filter
        filtered_movies = selected_movies[selected_movies['id'].isin(ratings_data['movieId'])]

        # Select 30 random movies
        random_movies = filtered_movies.sample(n=30)
        
        # Get movie details and movieIds
        movie_ids = random_movies['id'].tolist()
        movie_details_list = []
        for movie_id in movie_ids:
            movie_details = get_movie_details(movie_id)
            if movie_details:
                movie_details['id'] = int(movie_id)
                movie_details_list.append(movie_details)

        return jsonify(movie_details_list)

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': 'An error occurred while processing your request.'}), 500

    try:
        db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '54zs106ve449',
            'database': 'recom'
        }

        conn = mysql.connector.connect(**db_config)
        data_query = "SELECT movieId FROM ratings_small"
        ratings_data = pd.read_sql_query(data_query, conn)
        conn.close()

        selected_movies = pd.read_csv("/Users/ahmetyasirozcan/Desktop/Homeworks/recommendation_systems/archive/selected_movies.csv")
        selected_movies['id'] = pd.to_numeric(selected_movies['id'], errors='coerce', downcast='integer')

        # Find common Id's and filter
        filtered_movies = selected_movies[selected_movies['id'].isin(ratings_data['movieId'])]

        # Select 30 random movies
        random_movies = filtered_movies.sample(n=30)
        
        # Get movie details and movieIds
        movie_ids = random_movies['id'].tolist()
        movie_details_list = []
        for movie_id in movie_ids:
            movie_details = get_movie_details(movie_id)
            if movie_details:
                movie_details_with_id = {'id': int(movie_id), 'details': movie_details}
                movie_details_list.append(movie_details_with_id)

        # Get movieIds as a list
        movie_ids_list = [int(movie_id) for movie_id in movie_ids]

        return jsonify({'movie_details': movie_details_list, 'movie_ids': movie_ids_list})

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': 'An error occurred while processing your request.'}), 500

    try:
        db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '54zs106ve449',
            'database': 'recom'
        }

        conn = mysql.connector.connect(**db_config)
        data_query = "SELECT movieId FROM ratings_small"
        ratings_data = pd.read_sql_query(data_query, conn)
        conn.close()

        selected_movies = pd.read_csv("/Users/ahmetyasirozcan/Desktop/Homeworks/recommendation_systems/archive/selected_movies.csv")
        selected_movies['id'] = pd.to_numeric(selected_movies['id'], errors='coerce', downcast='integer')

        # Find common Id's and filter
        filtered_movies = selected_movies[selected_movies['id'].isin(ratings_data['movieId'])]

        # Select 30 random movies
        random_movies = filtered_movies.sample(n=30)
        
        # Get movie details and movieIds
        movie_ids = random_movies['id'].tolist()
        movie_details_list = []
        for movie_id in movie_ids:
            movie_details = get_movie_details(movie_id)
            if movie_details:
                movie_details_with_id = {'id': int(movie_id), 'details': movie_details}
                movie_details_list.append(movie_details_with_id)

        # Get movieIds as a list
        movie_ids_list = [int(movie_id) for movie_id in movie_ids]

        return jsonify({'movie_details': movie_details_list, 'movie_ids': movie_ids_list})

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({'error': 'An error occurred while processing your request.'}), 500


    try:
        # Gelen veriyi JSON formatında al
        data = request.json

        # Kullanıcı kimliği ve favori filmlerin kimliklerini al
        user_id = data.get('user_id')
        movie_ids = data.get('movie_ids')

        # Favori filmleri kullanıcı için veritabanına ekleyen fonksiyonu çağır
        result = add_favorite_movies(user_id, movie_ids)

        if result['success']:
            return jsonify({'message': 'Favorite movies added successfully.'}), 200
        else:
            return jsonify({'error': 'An error occurred while processing your request.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/add_favorite_movies', methods=['POST'])
def add_favorite_movies():
    try:
        # Gelen veriyi JSON formatında al
        data = request.json

        # Kullanıcı kimliği ve favori filmlerin kimliklerini al
        user_id_str = data.get('user_id')
        movie_ids = data.get('movie_ids')

        # Kullanıcı kimliğini benzersiz bir tamsayıya dönüştür
        user_id = generate_unique_id(user_id_str)

        # Her film için kullanıcı-film ilişkisini veritabanına ekle
        db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '54zs106ve449',
            'database': 'recom'
        }
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        for movie_id in movie_ids:
            # SQL sorgusu
            sql = "INSERT INTO ratings_small (userId, movieId, rating) VALUES (%s, %s, %s)"
            # Parametreler
            val = (user_id, movie_id, 5)  # Kullanıcının tüm favori filmlerine 5 puan veriyoruz
            # Sorguyu çalıştırma
            cursor.execute(sql, val)

        # Değişiklikleri kaydetme ve bağlantıyı kapatma
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Favorite movies added successfully.', 'user_id': user_id}), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
