import React from 'react';
import Home from './pages/Home';  // импортируем Home
import './App.css';
import { BrowserRouter } from 'react-router-dom';
import { Routes, Route, Link } from 'react-router-dom';
import Chats_page from './pages/Chats-page';
import LikesPage from './pages/Likes-page';
import User_Profile from './pages/User-profile';

function App() {
  return (
    <div className="app">
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/User-profile" element={<User_Profile />} />
        <Route path="/Likes-page" element={<LikesPage />} />
        <Route path="/Chats-page" element={<Chats_page />} />
      </Routes>
    </div>
  );
}

export default App;