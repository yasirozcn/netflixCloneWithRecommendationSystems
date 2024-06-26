from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
import mysql.connector
import requests
import random
from hashlib import sha256


app = Flask(__name__)
CORS(app)

def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# CORS başlıklarını her yanıt için ekleyin
@app.after_request
def after_request(response):
    return add_cors_headers(response)

def item_based_recommendation(movie_title, min_ratings=40, top_n=10):
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'koolay',
        'database': 'recom'
    }

    conn = mysql.connector.connect(**db_config)

    data_query = "SELECT * FROM ratings_small"
    data = pd.read_sql_query(data_query, conn)

    conn.close()

    selected_columns = pd.read_csv("C:/Users/Yasir Özcan/OneDrive/Masaüstü/netflix-recom/archive/selected_movies.csv")

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
        'password': 'koolay',
        'database': 'recom'
    }

    conn = mysql.connector.connect(**db_config)

    data_query = "SELECT * FROM ratings_small"
    ratings = pd.read_sql_query(data_query, conn)

    conn.close()

    selected_columns = pd.read_csv("C:/Users/Yasir Özcan/OneDrive/Masaüstü/netflix-recom/archive/selected_movies.csv")
    
    selected_columns = selected_columns.rename(columns={"id": "movieId"})
    movie_names = selected_columns.copy()
    movie_names['movieId'] = pd.to_numeric(movie_names['movieId'], errors='coerce', downcast='integer')
    movie_names = movie_names.dropna(subset=['movieId']).astype({'movieId': 'int'})
    movie_names = movie_names.sort_values(by='movieId')
    
    merged_data = pd.merge(ratings, movie_names, on='movieId', how='inner')
    merged_data.drop('timestamp', axis=1, inplace=True)
    
    agg_ratings = merged_data.groupby('original_title').agg(mean_rating=('rating', 'mean'),
                                                            number_of_ratings=('rating', 'count')).reset_index()

    matrix = merged_data.pivot_table(index='userId', columns='original_title', values='rating')
    matrix_norm = matrix.subtract(matrix.mean(axis=1), axis='rows')
    
    scaler = MinMaxScaler()
    matrix_norm_scaled = pd.DataFrame(scaler.fit_transform(matrix_norm), index=matrix_norm.index, columns=matrix_norm.columns)
    
    user_similarity_cosine = cosine_similarity(matrix_norm_scaled.fillna(0))
    user_similarity_cosine_df = pd.DataFrame(user_similarity_cosine, index=matrix_norm_scaled.index, columns=matrix_norm_scaled.index)
    scaler = MinMaxScaler()
    user_similarity_normalized = pd.DataFrame(scaler.fit_transform(user_similarity_cosine_df), index=user_similarity_cosine_df.index, columns=user_similarity_cosine_df.columns)

    # New: Include the new user's data
    if user_id not in matrix_norm_scaled.index:
        matrix_norm_scaled.loc[user_id] = None
        user_similarity_normalized[user_id] = None

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


@app.route('/movies/details', methods=['GET'])
def get_filtered_movie_details():
    try:
        # Database connection and ratings retrieval
        db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'koolay',
            'database': 'recom'
        }

        conn = mysql.connector.connect(**db_config)
        data_query = "SELECT movieId FROM ratings_small"
        ratings_data = pd.read_sql_query(data_query, conn)
        conn.close()

        # Load and convert selected movies' Id to int
        selected_movies = pd.read_csv("C:/Users/Yasir Özcan/OneDrive/Masaüstü/netflix-recom/archive/selected_movies.csv")
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

    movie_ids = recommendations['movieId'].tolist()
    movie_details_list = []

    for movie_id in movie_ids:
        movie_details = get_movie_details(movie_id)
        if movie_details:
            movie_details['real_title'] = movie_details.get('title')  # Real title
            movie_details.pop('title')  # Remove 'title'
            # Her bir film için movie_details ve recommendations verileri bir araya getiriliyor
            movie_details_with_recommendations = {
                'movie_details': movie_details,
                'recommendations': recommendations.loc[recommendations['movieId'] == movie_id].to_dict(orient='records')[0]
            }
            movie_details_list.append(movie_details_with_recommendations)

    return jsonify(movie_details_list)


@app.route('/ub', methods=['GET'])
def user_based_recommend():
    user_id = request.args.get('user_id')

    recommendations = recommend_movies_for_user(user_id)

    movie_ids = recommendations['movieId'].tolist()
    movie_details_list = []

    for movie_id in movie_ids:
        movie_details = get_movie_details(movie_id)
        if movie_details:
            movie_details['real_title'] = movie_details.get('title')  # Real title
            movie_details.pop('title')  # Remove 'title'
            # Her bir film için movie_details ve recommendations verileri bir araya getiriliyor
            movie_details_with_recommendations = {
                'movie_details': movie_details,
                'recommendations': recommendations.loc[recommendations['movieId'] == movie_id].to_dict(orient='records')[0]
            }
            movie_details_list.append(movie_details_with_recommendations)

    return jsonify(movie_details_list)


@app.route('/new', methods=['GET'])
def get_random_movies():
    try:
        # Veritabanı bağlantı bilgileri
        db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'koolay',
            'database': 'recom'
        }

        # Veritabanına bağlan
        conn = mysql.connector.connect(**db_config)

        # Filmlerin puanlamalarını içeren verileri al
        data_query = "SELECT movieId FROM ratings_small GROUP BY movieId HAVING COUNT(*) > 40"
        ratings_data = pd.read_sql_query(data_query, conn)

        # Bağlantıyı kapat
        conn.close()

        # Seçilen filmlerin bulunduğu CSV dosyasını yükle
        selected_movies = pd.read_csv("C:/Users/Yasir Özcan/OneDrive/Masaüstü/netflix-recom/archive/selected_movies.csv")
        selected_movies['id'] = pd.to_numeric(selected_movies['id'], errors='coerce', downcast='integer')

        # Ortak ID'leri bul ve filtrele
        filtered_movies = selected_movies[selected_movies['id'].isin(ratings_data['movieId'])]

        # 30 rastgele film seç
        random_movies = filtered_movies.sample(n=30)
        
        # Filmlerin detaylarını ve ID'lerini al
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


    
@app.route('/add_favorite_movies', methods=['POST'])
def add_favorite_movies():
    try:
        # Gelen veriyi JSON formatında al
        data = request.json

        # Kullanıcı kimliği, favori filmlerin kimlikleri ve puanı al
        user_id = data.get('user_id')
        movies = data.get('movies')  # Her film için {movie_id, rating} olacak

        # Her film için kullanıcı-film ilişkisini veritabanına ekle
        db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': 'koolay',
            'database': 'recom'
        }
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        for movie in movies:
            movie_id = movie.get('movie_id')
            rating = movie.get('rating')
            # SQL sorgusu
            sql = "INSERT INTO ratings_small (userId, movieId, rating) VALUES (%s, %s, %s)"
            # Parametreler
            val = (user_id, movie_id, rating)
            # Sorguyu çalıştırma
            cursor.execute(sql, val)

        # Değişiklikleri kaydetme ve bağlantıyı kapatma
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Favorite movies added successfully.', 'user_id': user_id}), 200

    except Exception as e:
        print("Hata:", e)
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
