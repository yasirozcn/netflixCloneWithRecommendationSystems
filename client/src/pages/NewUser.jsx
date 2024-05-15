/* eslint-disable no-unused-vars */
/* eslint-disable react/prop-types */
import React, { useEffect, useState } from "react";
import "../styles/new.css";
import { useNavigate } from "react-router-dom";

function NewUser({ user, submitMovies }) {
  const [random, setRandom] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMovies, setSelectedMovies] = useState([]);
  const [selectedCount, setSelectedCount] = useState(selectedMovies.length); // Başlangıçta seçilen film sayısını al
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

  useEffect(() => {
    setSelectedCount(selectedMovies.length); // Seçilen film sayısını güncelle
  }, [selectedMovies]); // Seçilen filmler değiştiğinde bu etkileşim gerçekleşir

  const handleMovieClick = (event, id) => {
    event.preventDefault();

    const index = selectedMovies.indexOf(id);
    if (index === -1) {
      if (selectedCount < 10) {
        setSelectedMovies((prevSelectedMovies) => [...prevSelectedMovies, id]);
      } else {
        alert("10 tane film seçtiniz daha fazla seçemezsiniz :(");
      }
    } else {
      const newSelectedMovies = [...selectedMovies];
      newSelectedMovies.splice(index, 1);
      setSelectedMovies(newSelectedMovies);
    }
  };

  const handleSubmit = () => {
    submitMovies(selectedMovies);
  };

  const handleRefresh = () => {
    setLoading(true);
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
  };

  return (
    <div className="new">
      <div className="top">
        <h1>
          Lütfen en beğendiğiniz en az 5 en fazla 10 film seçin. Seçilen film
          sayısı: {selectedCount}
        </h1>
        <button
          className={selectedMovies.length < 5 ? "hide" : ""}
          onClick={handleSubmit}
        >
          Gönder
        </button>
        <button onClick={handleRefresh}>Yenile</button>
      </div>

      <div className="new__container">
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
