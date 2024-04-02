// eslint-disable-next-line no-unused-vars
import React, { useState, useEffect } from "react";
import { BiPlay } from "react-icons/bi";
import { RiInformationLine } from "react-icons/ri";
import "../styles/banner.css";
function Banner() {
  const [movieDetails, setMovieDetails] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('http://127.0.0.1:5000/movies/details')
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        setMovieDetails(data);
        setLoading(false);
      })
      .catch(error => {
        console.error('There was a problem with the fetch operation:', error);
        setError(error);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  return (
    <header
      className="banner"
      style={{
        backgroundSize: "cover",
        backgroundImage: `url("https://image.tmdb.org/t/p/original/${movieDetails[0].poster_path}")`,
        backgroundPosition: "center center",
      }}
    >
      <div className="banner__contents">
        <h1 className="banner__title">{movieDetails[0].title}</h1>
        <h1 className="banner__description">
          {movieDetails[0].overview}
        </h1>
        <div className="banner__buttons">
          <button className="banner__button">
            <BiPlay className="banner__icons" /> Oynat
          </button>
          <button className="banner__button">
            <RiInformationLine className="banner__icons" /> Daha fazla bilgi
          </button>
        </div>
      </div>
    </header>
  );
}

export default Banner;
