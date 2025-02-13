# Netflix Clone with Movie Recommendation System

A full-stack web application that replicates Netflix's core functionality with an advanced movie recommendation system. The project uses collaborative filtering and content-based recommendations to suggest movies to users based on their preferences and viewing history.

## Features

- User authentication and authorization
- Movie browsing with detailed information
- Personalized movie recommendations
- Rating system for movies
- Responsive Netflix-like interface
- Advanced recommendation algorithms:
  - Item-based collaborative filtering
  - User-based collaborative filtering
  - Content-based recommendations

## Tech Stack

### Frontend
- React.js
- Vite
- Tailwind CSS
- Axios for API calls

### Backend
- Python
- Flask
- MySQL
- Pandas
- Scikit-learn
- NumPy

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.8+
- Node.js 14+
- MySQL 8.0+
- Git

## Installation

1. Clone the repository

2. Set up the backend
Create and activate virtual environment
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
Install dependencies
pip install -r requirements.txt
Configure MySQL
Create a database named 'recom'
mysql -u root -p
CREATE DATABASE recom;
Import the database schema and data
mysql -u root -p recom < database/schema.sql

3. Set up the frontend


## Configuration

1. Backend Configuration (BE/app.py)
python
db_config = {
'host': 'localhost',
'user': 'your_mysql_username',
'password': 'your_mysql_password',
'database': 'recom'
}

2. Frontend Configuration (FE/src/config.js)
javascript
export const API_BASE_URL = 'http://localhost:5000';


## Running the Application

1. Start the Backend Server
2. Start the Frontend Development Server


## Database Structure

The application uses a MySQL database with the following main tables:
- `users`: Stores user information
- `ratings`: Stores movie ratings by users
- `movies`: Stores movie information

## API Endpoints

### Movie Endpoints
- `GET /movies/details`: Get filtered movie details
- `GET /new`: Get random movie recommendations
- `POST /add_favorite_movies`: Add movies to user's favorites

### Recommendation Endpoints
- `GET /recommend`: Get personalized movie recommendations
- `GET /item-based`: Get item-based recommendations

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## Acknowledgments

- Movie dataset from TMDB
- Netflix for design inspiration
- Collaborative filtering algorithms based on research papers

## Contact

Ahmet Yasir ÖZCAN -(yasirozcn@gmail.com)
Project Link: [https://github.com/yasirozcn/netflixCloneWithRecommendationSystems]