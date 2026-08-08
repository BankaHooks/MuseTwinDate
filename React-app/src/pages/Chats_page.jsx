import { useState } from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import '../styles/Chats-page.css';

const Chats_page = () => {
  const base = import.meta.env.BASE_URL || '/';

  const chats = [
    {
      id: 1,
      name: 'Maria',
      lastMessage: 'Hello! I like Beatles too!',
      time: '12:34',
      avatar: 'UserCard.png',
    },
    {
      id: 2,
      name: 'Anna',
      lastMessage: 'Listen this one, that`s awesome',
      time: 'вчера',
      avatar: 'UserCard.png',
    },
    {
      id: 3,
      name: 'Elena',
      lastMessage: 'Can we meet someday?',
      time: 'вчера',
      avatar: 'UserCard.png',
    },
    {
      id: 4,
      name: 'Olga',
      lastMessage: 'Good night',
      time: 'пн',
      avatar: 'UserCard.png',
    },
    {
      id: 5,
      name: 'Natalia',
      lastMessage: 'Nice playlist   ',
      time: 'вс',
      avatar: 'UserCard.png',
    },
  ];

  return (
    <div
      className="User-style"
      style={{
        backgroundImage: `url(${base}background_new.png)`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        minHeight: '100vh',
        backgroundRepeat: 'no-repeat',
      }}
    >
      <Header showActions={false} />
      <div className="chats-grid">
        {chats.map((chat) => (
          <div key={chat.id} className="chat-item">
            <img
              src={`${base}${chat.avatar}`}
              alt={chat.name}
              className="chat-avatar"
            />
            <div className="chat-info">
              <div className="chat-name">{chat.name}</div>
              <div className="chat-last-message">{chat.lastMessage}</div>
            </div>
            <div className="chat-time">{chat.time}</div>
          </div>
        ))}
      </div>
      <Footer />
    </div>
  );
};

export default Chats_page;