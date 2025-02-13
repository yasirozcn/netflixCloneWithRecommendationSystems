from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
import mysql.connector
import requests
import random
from hashlib import sha256
from scipy.sparse import csr_matrix
import numpy as np


app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# CORS başlıklarını her yanıt için ekleyin
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

def item_based_recommendation(movie_title, min_ratings=40, top_n=10):
    try:
        print(f"\n[DEBUG] Film bazlı öneri başlangıç: film={movie_title}")
        
        db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '54zs106ve449',
            'database': 'recom'
        }

        conn = mysql.connector.connect(**db_config)

        # MySQL uyumlu sorgu
        data_query = """
            WITH popular_movies AS (
                SELECT movieId 
                FROM ratings 
                GROUP BY movieId 
                HAVING COUNT(*) > 40
                ORDER BY COUNT(*) DESC
                LIMIT 1000
            )
            SELECT r.* 
            FROM ratings r
            JOIN popular_movies pm ON r.movieId = pm.movieId
        """
        
        print("[DEBUG] SQL sorgusu çalıştırılıyor...")
        data = pd.read_sql_query(data_query, conn)
        print(f"[DEBUG] Veri çekildi. Şekil: {data.shape}")

        conn.close()

        # CSV'den sadece gerekli sütunları oku
        selected_columns = pd.read_csv("/Users/ahmetyasirozcan/Documents/Projects/netflixCloneWithRecommendationSystems/BE/archive/movies_metadata.csv",
                                     usecols=['id', 'original_title'])

        selected_columns = selected_columns.rename(columns={"id": "movieId"})
        selected_columns['movieId'] = pd.to_numeric(selected_columns['movieId'], errors='coerce', downcast='integer')
        selected_columns = selected_columns.dropna(subset=['movieId'])
        
        # Veri birleştirme
        merged_data = pd.merge(data, selected_columns, on='movieId', how='inner')
        print(f"[DEBUG] Veriler birleştirildi. Şekil: {merged_data.shape}")

        # Pivot table oluştur
        table = merged_data.pivot_table(index="userId", columns="original_title", values="rating")
        print("[DEBUG] Pivot table oluşturuldu")

        if movie_title not in table.columns:
            print(f"[DEBUG] Film bulunamadı: {movie_title}")
            return pd.DataFrame(columns=['movieId', 'movieName', 'Correlation', 'number_of_ratings'])

        # Benzerlik hesaplama
        recommend = table[movie_title]
        correlation = table.corrwith(recommend)
        correlation_dataframe = pd.DataFrame(correlation, columns=["Correlation"])
        correlation_dataframe.dropna(inplace=True)
        
        print("[DEBUG] Korelasyon hesaplandı")

        # Rating sayılarını hesapla
        ratings = pd.DataFrame(merged_data.groupby("original_title")["rating"].agg(['mean', 'count']))
        correlation_dataframe = correlation_dataframe.join(ratings['count'])
        correlation_dataframe = correlation_dataframe.rename(columns={'count': 'number_of_ratings'})

        # Final önerileri oluştur
        final_recommendation = correlation_dataframe[
            correlation_dataframe["number_of_ratings"] > min_ratings
        ].sort_values("Correlation", ascending=False)[:top_n]
        
        final_recommendation = final_recommendation.reset_index()
        final_recommendation = pd.merge(
            final_recommendation, 
            selected_columns, 
            left_on='original_title', 
            right_on='original_title', 
            how='left'
        )
        final_recommendation = final_recommendation.rename(columns={
            "movieId": "movieId", 
            "original_title": "movieName"
        })

        print("[DEBUG] Öneriler oluşturuldu")
        print(final_recommendation[['movieId', 'movieName', 'Correlation', 'number_of_ratings']])

        return final_recommendation[['movieId', 'movieName', 'Correlation', 'number_of_ratings']]

    except Exception as e:
        print(f"[ERROR] Film bazlı öneri hatası: {str(e)}")
        raise e

def recommend_movies_for_user(user_id, n=10, user_similarity_threshold=0.2, m=10):
    try:
        print(f"\n[DEBUG] Başlangıç: user_id={user_id}")
        
        db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '54zs106ve449',
            'database': 'recom'
        }

        conn = mysql.connector.connect(**db_config)
        print("[DEBUG] Veritabanı bağlantısı başarılı")

        # Veri setini daha da küçült
        data_query = """
            WITH popular_movies AS (
                SELECT movieId 
                FROM ratings 
                GROUP BY movieId 
                HAVING COUNT(*) > 100
                LIMIT 500
            ),
            recent_users AS (
                SELECT DISTINCT userId 
                FROM ratings 
                ORDER BY userId DESC 
                LIMIT 5000
            )
            SELECT r.userId, r.movieId, r.rating
            FROM ratings r
            JOIN recent_users u ON r.userId = u.userId
            JOIN popular_movies m ON r.movieId = m.movieId
        """
        
        print("[DEBUG] SQL sorgusu çalıştırılıyor...")
        ratings = pd.read_sql_query(data_query, conn)
        print(f"[DEBUG] Veri çekildi. Şekil: {ratings.shape}")

        conn.close()

        # CSV'den sadece gerekli sütunları oku
        selected_columns = pd.read_csv("/Users/ahmetyasirozcan/Documents/Projects/netflixCloneWithRecommendationSystems/BE/archive/movies_metadata.csv", 
                                     usecols=['id', 'original_title'])
        
        selected_columns = selected_columns.rename(columns={"id": "movieId"})
        selected_columns['movieId'] = pd.to_numeric(selected_columns['movieId'], errors='coerce', downcast='integer')
        selected_columns = selected_columns.dropna(subset=['movieId'])
        
        # Veri birleştirme
        merged_data = pd.merge(ratings, selected_columns, on='movieId', how='inner')
        print(f"[DEBUG] Veriler birleştirildi. Şekil: {merged_data.shape}")

        # Kullanıcı-film matrisi oluştur (sparse matrix)
        user_ids = merged_data['userId'].unique()
        movie_ids = merged_data['movieId'].unique()
        
        user_to_idx = {uid: i for i, uid in enumerate(user_ids)}
        movie_to_idx = {mid: i for i, mid in enumerate(movie_ids)}
        
        ratings_sparse = csr_matrix(
            (merged_data['rating'],
             (merged_data['userId'].map(user_to_idx),
              merged_data['movieId'].map(movie_to_idx)))
        )
        
        # Benzerlik hesaplama (batch işleme ile)
        batch_size = 1000
        n_users = len(user_ids)
        similarities = np.zeros((n_users, n_users))
        
        for i in range(0, n_users, batch_size):
            end = min(i + batch_size, n_users)
            batch = ratings_sparse[i:end]
            similarities[i:end] = cosine_similarity(batch, ratings_sparse)
        
        user_similarity_df = pd.DataFrame(
            similarities,
            index=user_ids,
            columns=user_ids
        )
        
        print("[DEBUG] Benzerlik hesaplaması tamamlandı")
        
        if user_id not in user_similarity_df.columns:
            print(f"[DEBUG] Yeni kullanıcı: {user_id}")
            # Yeni kullanıcı için popüler filmleri öner
            popular_movies = merged_data.groupby('movieId').agg({
                'rating': ['mean', 'count'],
                'original_title': 'first'
            }).reset_index()
            popular_movies.columns = ['movieId', 'movie_score', 'rating_count', 'original_title']
            popular_movies = popular_movies[popular_movies['rating_count'] > 50]
            return popular_movies.sort_values('movie_score', ascending=False)[['movieId', 'original_title', 'movie_score']].head(m)

        # En benzer kullanıcıları bul
        similar_users = user_similarity_df[user_id].nlargest(n+1)[1:]
        
        # Önerileri hesapla
        recommendations = merged_data[
            merged_data['userId'].isin(similar_users.index)
        ].groupby(['movieId', 'original_title']).agg({
            'rating': ['mean', 'count']
        }).reset_index()
        
        recommendations.columns = ['movieId', 'original_title', 'movie_score', 'rating_count']
        recommendations = recommendations[recommendations['rating_count'] > 10]
        recommendations = recommendations.sort_values('movie_score', ascending=False).head(m)
        
        print("[DEBUG] Öneriler oluşturuldu")
        print(recommendations[['movieId', 'original_title', 'movie_score']])
        
        return recommendations[['movieId', 'original_title', 'movie_score']]

    except Exception as e:
        print(f"[ERROR] Hata oluştu: {str(e)}")
        raise e

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
            'password': '54zs106ve449',
            'database': 'recom'
        }

        conn = mysql.connector.connect(**db_config)
        data_query = "SELECT movieId FROM ratings"
        ratings_data = pd.read_sql_query(data_query, conn)
        conn.close()

        # Load and convert selected movies' Id to int
        selected_movies = pd.read_csv("/Users/ahmetyasirozcan/Documents/Projects/netflixCloneWithRecommendationSystems/BE/archive/movies_metadata.csv")
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
            'password': '54zs106ve449',
            'database': 'recom'
        }

        # Veritabanına bağlan
        conn = mysql.connector.connect(**db_config)

        # Filmlerin puanlamalarını içeren verileri al
        data_query = "SELECT movieId FROM ratings GROUP BY movieId HAVING COUNT(*) > 100"
        ratings_data = pd.read_sql_query(data_query, conn)

        # Bağlantıyı kapat
        conn.close()

        # Seçilen filmlerin bulunduğu CSV dosyasını yükle
        selected_movies = pd.read_csv("/Users/ahmetyasirozcan/Documents/Projects/netflixCloneWithRecommendationSystems/BE/archive/movies_metadata.csv")
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
            'password': '54zs106ve449',
            'database': 'recom'
        }
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        for movie in movies:
            movie_id = movie.get('movie_id')
            rating = movie.get('rating')
            # SQL sorgusu
            sql = "INSERT INTO ratings (userId, movieId, rating) VALUES (%s, %s, %s)"
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
