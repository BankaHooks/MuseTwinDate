import React from 'react';
import Home from './pages/Home';  // импортируем Home
import './App.css';
import { BrowserRouter } from 'react-router-dom';
import { Routes, Route, Link } from 'react-router-dom';

function App() {
  return (
    <BrowserRouter>
    <div className="app">
      <Home />
    </div>
    </BrowserRouter>
  );
}

export default App;