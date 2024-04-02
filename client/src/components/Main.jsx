// eslint-disable-next-line no-unused-vars
import React, { useEffect, useState } from "react";
import "../styles/main.css";

function Main() {
  const [movieDetails, setMovieDetails] = useState([]);

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
    fetch("http://127.0.0.1:5000/movies/details")
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
  }, []);

  return (
    <div className="row">
      <h1>All Movie Details</h1>
      <ul className="main__container">
        {movieDetails.map((movie) => (
          <li key={movie.title} className="main__list">
            <img
              src={`https://image.tmdb.org/t/p/original/${movie.poster_path}`}
              alt={movie.title}
              onClick={() => getRecommendations("ib", movie.title)}
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
