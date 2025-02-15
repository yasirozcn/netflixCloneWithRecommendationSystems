/* eslint-disable no-unused-vars */
/* eslint-disable react/prop-types */
/* eslint-disable react/jsx-key */
import React, { useEffect, useState } from "react";
import "../styles/main.css";
import { AiFillLike } from "react-icons/ai";
import { AiFillDislike } from "react-icons/ai";

function Main({ user, submitMovies }) {
  const [movieDetails, setMovieDetails] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);

  function getRecommendations(type, movieTitle) {
    setLoading(true);
    const encodedTitle = encodeURIComponent(movieTitle);
    
    fetch(`http://127.0.0.1:5000/${type}?movie_title=${encodedTitle}`, {
      method: 'GET',
      credentials: 'include',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      }
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        setRecommendations(data);
        setLoading(false);
        if (data.length === 0) {
          console.log("No recommendations found.");
        }
      })
      .catch((error) => {
        setLoading(false);
        console.error("Error:", error);
      });
  }

  useEffect(() => {
    if (user && user.uid) {
      setLoading(true);
      fetch(`http://127.0.0.1:5000/ub?user_id=${user.uid}`)
        .then((response) => {
          if (!response.ok) {
            throw new Error("Network response was not ok");
          }
          return response.json();
        })
        .then((data) => {
          setMovieDetails(data);
          setLoading(false);
        })
        .catch((error) => {
          setLoading(false);
          console.error("There was a problem with the fetch operation:", error);
        });
    }
  }, [user]);

  const addToFavorites = (movieId) => {
    submitMovies([movieId], 5);
    console.log(`Added to favorites: ${movieId}`);
  };
  const dislike = (movieId) => {
    submitMovies([movieId], 1);
    console.log(`Disliked: ${movieId}`);
  }

  return (
    <>
      <div className="row">
        <h1>All Movie Details</h1>
        <ul className="main__container">
          {movieDetails.map((movie) => (
            <li key={movie.movie_details.real_title} className="main__list">
              <img
                src={`https://image.tmdb.org/t/p/original/${movie.movie_details.poster_path}`}
                alt={movie.movie_details.real_title}
                onClick={() => {
                  getRecommendations(
                    "ib",
                    movie.recommendations.original_title
                  );
                  console.log(movie.recommendations.movieId);
                }}
              />
              <button
                className="favoriteButton"
                onClick={() => addToFavorites(movie.recommendations.movieId)}
              >
                <AiFillLike />
              </button>
              <button className="dislikeButton" onClick={()=>dislike(movie.recommendations.movieId)}><AiFillDislike/></button>
            </li>
          ))}
        </ul>
      </div>
      {loading ? (
        <div className="row loading"></div>
      ) : recommendations.length > 0 ? (
        <div className="row">
          <h1>Recommended Movie Details</h1>
          <ul className="main__container">
            {recommendations.map((movie) => (
              <li className="main__list">
                <img
                  src={`https://image.tmdb.org/t/p/original/${movie.movie_details.poster_path}`}
                  alt={movie.movie_details.real_title}
                  onClick={() =>
                    getRecommendations("ib", movie.recommendations.movieName)
                  }
                />
                <button
                  className="favoriteButton"
                  onClick={() => addToFavorites(movie.recommendations.movieId)}
                >
                  <AiFillLike />
                </button>
                <button className="dislikeButton" onClick={()=>dislike(movie.recommendations.movieId)}><AiFillDislike/></button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </>
  );
}

export default Main;
