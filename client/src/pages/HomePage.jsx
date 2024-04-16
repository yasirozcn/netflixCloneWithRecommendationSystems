/* eslint-disable react/prop-types */
// eslint-disable-next-line no-unused-vars
import React from "react";
import Navbar from "../components/Navbar";
import Banner from "../components/Banner";
import Main from "../components/Main";

function HomePage({ user }) {
  return (
    <div>
      <Navbar />
      <Banner />
      <Main user={user} />
    </div>
  );
}

export default HomePage;
