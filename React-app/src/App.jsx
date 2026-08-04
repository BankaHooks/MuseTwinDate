import './App.css';

function App() {
    const user = {
      name: "Igor Colomoyski",
      age: 27,
      bio: "I`m just cool ukrainian guy",
      photo: "/UserCard.png",
    };

    return (
      <div className="app">
        <header className="header">
        <div className="Header-box">
            <div className="left-part">
                <button className="Filters-Button">
                    <img src="/list.svg" alt="" className="filter-icon" />
                    Filters
                </button>
            </div>
            <div className="middle-part">
                <h2 className="App-name">
                    MuseTwin
                </h2>            
            </div>
            <div className="right-part">
                <button className="Report-Button">
                    <img src="/danger.svg" alt="" className="report-icon" />
                    Report
                </button>
            </div>
        </div>
    </header>
    <div id="main-page" className="page">
        <div className="Main-box">
            <div className="User-full-card">
                <div className="User-photo-card">
                    <img src="/UserCard.png" alt="User-photo" className="Photo-of-User" />
                    <div className="Box-for-text">
                        <h4 className="User-name">Igor Colomoyski, 27</h4>
                        <h5 className="Text-from-User">I`m just cool ukrainian guy</h5>
                    </div>
                </div>
                <div className="Users-music-stats">
                    Lorem ipsum dolor sit amet consectetur adipisicing elit. Ex saepe veniam, molestiae eum magnam sint. Sunt dicta, sapiente maiores voluptate perspiciatis maxime enim praesentium eos ullam consequuntur quisquam vero nesciunt.
                </div>
            </div>
            <div className="side-bar">
                <div className="sidebar-buttons">
                    <img src="../public/UserPhoto.png" alt="User-Photo" className="sidebar-user_photo" />
                    <button className="Like-button">
                        <img src="../public/user-add.svg" alt="" className="like-icon" />
                    </button>
                    <button className="Chat-button">
                        <img src="../public/chat-icon-png.png" alt="" className="chat-icon" />
                    </button>
                    <button className="Skip-button">
                        <img src="../public/skip-button.svg" alt="" className="skip-icon" />
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <footer className="Choose-page-box">
        <div className="footer-buttons">
            <button className="Main-page">
                <img src="../public/home.svg" alt="" />
            </button>
            <button className="Likes-page">
                <img src="../public/heart.svg" alt="" />
            </button>
            <button className="Chats-page">
                <img src="../public/mail.svg" alt="" />
            </button>
            <button className="Profile-page">
                <img src="../public/smile.svg" alt="" />
            </button>
        </div>
    </footer>
      </div>
    )
}

export default App
