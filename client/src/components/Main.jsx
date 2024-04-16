/* eslint-disable react/prop-types */
// eslint-disable-next-line no-unused-vars
import React, { useEffect, useState } from "react";
import "../styles/main.css";

function Main({ user }) {
  const [movieDetails, setMovieDetails] = useState([]);
  console.log("yasir", user);
  function getRecommendations(type, movieTitle) {
    fetch(`http://127.0.0.1:5000/${type}?movie_title=${movieTitle}`)
      .then((response) => response.json())
      .then((data) => {
        console.log(data);
        if (data.length === 0) {
          console.log("No recommendations found.");
        } else {
          data.forEach((movie) => {
            console.log(
              `${movie.movieName} - Correlation: ${movie.Correlation} - Number of Ratings: ${movie.number_of_ratings}`
            );
          });
        }
      })
      .catch((error) => console.error("Error:", error));
  }

  useEffect(() => {
    // Check if user is logged in
    if (user && user.uid) {
      fetch(`http://127.0.0.1:5000/ub?user_id=${user.uid}`)
        .then((response) => {
          if (!response.ok) {
            throw new Error("Network response was not ok");
          }
          return response.json();
        })
        .then((data) => {
          setMovieDetails(data);
        })
        .catch((error) => {
          console.error("There was a problem with the fetch operation:", error);
        });
    }
  }, [user]);
  console.log("abc", movieDetails);
  return (
    <div className="row">
      <h1>All Movie Details</h1>
      <ul className="main__container">
        {movieDetails.map((movie) => (
          <li key={movie.movie_details.real_title} className="main__list">
            <img
              src={`https://image.tmdb.org/t/p/original/${movie.movie_details.poster_path}`}
              alt={movie.movie_details.real_title}
              onClick={() =>
                getRecommendations("ib", movie.recommendations.original_title)
              }
            />
            {/* <h2>{movie.title}</h2> */}
            {/* <p>{movie.overview}</p> */}
            {/* <p>Release Date: {movie.release_date}</p> */}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default Main;
