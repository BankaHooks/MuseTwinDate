import React from 'react';
import Home from './pages/Home';  // импортируем Home
import './App.css';
import { BrowserRouter } from 'react-router-dom';
import { Routes, Route, Link } from 'react-router-dom';
import Chats_page from './pages/Chats_page';
import Likes_Page from './pages/Likes_page';
import User_Profile from './pages/User_profile';

function App() {
  return (
    <div className="app">
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/User_profile" element={<User_Profile />} />
        <Route path="/Likes_page" element={<Likes_Page />} />
        <Route path="/Chats_page" element={<Chats_page />} />
      </Routes>
    </div>
  );
}

export default App;