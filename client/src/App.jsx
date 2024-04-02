/* eslint-disable no-unused-vars */
import React, { useEffect, useState } from "react";
import "./App.css";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import { auth } from "./firebase";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Profiles from "./pages/Profiles";
import NewUser from "./pages/NewUser";

function App() {
  const [user, setUser] = useState({});

  const submitMovies = (selectedMovies) => {
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
        alert("Seçilen filmler başarı ile kaydedildi.");
        window.location.href = "/";
      })
      .catch((error) => {
        console.error("There was a problem with the fetch operation:", error);
        // Handle error
      });
  };

  useEffect(() => {
    auth.onAuthStateChanged((userAuth) => {
      if (userAuth) {
        setUser({ email: userAuth.email, uid: userAuth.uid });
      } else {
        console.log("error");
      }
    });
  }, []);

  console.log(user);
  console.log(user.email);

  return (
    <Router>
      {user.email === undefined || user.uid === undefined ? (
        <LoginPage />
      ) : (
        <Routes>
          <Route exect path="/" element={<HomePage />} />
          <Route
            path="/profile"
            element={<Profiles user={user} setUser={setUser} />}
          />
          <Route
            path="/new"
            element={<NewUser user={user} submitMovies={submitMovies} />}
          />
        </Routes>
      )}
    </Router>
  );
}

export default App;
