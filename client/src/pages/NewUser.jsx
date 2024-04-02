/* eslint-disable react/prop-types */
/* eslint-disable no-unused-vars */
import React, { useEffect, useState } from "react";
import "../styles/new.css";
import { useNavigate } from "react-router-dom";

function NewUser({ user }) {
  const [random, setRandom] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMovies, setSelectedMovies] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetch("http://127.0.0.1:5000/new")
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then((data) => {
        setRandom(data);
        setLoading(false);
      })
      .catch((error) => {
        console.error("There was a problem with the fetch operation:", error);
        setLoading(false);
      });
  }, []);

  const handleMovieClick = (event, id) => {
    event.preventDefault();

    const index = selectedMovies.indexOf(id);
    if (index === -1) {
      if (selectedMovies.length < 8) {
        setSelectedMovies((prevSelectedMovies) => [...prevSelectedMovies, id]);
      } else {
        alert("You have already selected 8 movies");
      }
    } else {
      const newSelectedMovies = [...selectedMovies];
      newSelectedMovies.splice(index, 1);
      setSelectedMovies(newSelectedMovies);
    }
  };
  const submitMovies = () => {
    fetch("http://127.0.0.1:5000/add_favorite_movies", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        user_id: user.uid,
        movie_ids: selectedMovies,
      }),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.json();
      })
      .then((data) => {
        console.log(data);
        alert("Selected movies were successfully recorded");
        navigate("/");
      })
      .catch((error) => {
        console.error("There was a problem with the fetch operation:", error);
        // Handle error
      });
  };
  console.log(selectedMovies);
  return (
    <div className="new">
      <div className="top">
        <h1>Please select at least 4 movies</h1>
        <button
          className={selectedMovies.length < 4 ? "hide" : ""}
          onClick={submitMovies}
        >
          Submit
        </button>
      </div>

      <div className="new__container">
        ß
        {loading ? (
          <div className="loading-overlay">
            <div className="loading-spinner"></div>
          </div>
        ) : (
          random.map((movie) => (
            <div
              key={movie.title}
              className={`new__item ${
                selectedMovies.includes(movie.title) ? "selected" : ""
              }`}
              onClick={(event) => handleMovieClick(event, movie.id)}
            >
              <img
                src={`https://image.tmdb.org/t/p/original/${movie.poster_path}`}
                alt={movie.title}
                className={selectedMovies.includes(movie.id) ? "tick" : ""}
              />
            </div>
          ))
        )}
      </div>
    </div>
  );
}

export default NewUser;
