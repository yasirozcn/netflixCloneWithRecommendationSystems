// eslint-disable-next-line no-unused-vars
import React from "react";
import "../styles/login.css";
import SignInScreen from "./SignInScreen";
import { useState } from "react";

// eslint-disable-next-line react/prop-types
function LoginPage({ user }) {
  const [signIn, setSignIn] = useState(false);
  return (
    <>
      <div className="loginScreen">
        <div className="loginScreen__background">
          <a href="/">
            <img
              className="loginScreen__logo"
              src="https://upload.wikimedia.org/wikipedia/commons/0/08/Netflix_2015_logo.svg"
              alt="Netflix Logo"
            />
          </a>
          <button
            onClick={() => {
              setSignIn(true);
            }}
            style={{ cursor: "pointer" }}
            className="loginScreen__button"
          >
            Giriş yap
          </button>
          <div className="loginScreen__gradient" />
        </div>
      </div>
      {signIn ? (
        <SignInScreen user={user} />
      ) : (
        <div className="loginScreen__body">
          <h1>Filmler, TV dizileri ve daha fazlası....</h1>
          <h2>İstedğin yerde izle. İstediğin zaman iptal et..</h2>
          <h3>
            İzlemeye hazır mısın? Kayıt olmak için şimdi e-posta adresini gir.
          </h3>
          <div className="loginScreen__input">
            <form>
              <input type="email" placeholder="E-posta Adresi" />
              <button
                onClick={() => {
                  setSignIn(true);
                }}
                className="loginScreen__getStarted"
              >
                Hadi Başlayalım
              </button>
            </form>
          </div>
        </div>
      )}
    </>
  );
}

export default LoginPage;
