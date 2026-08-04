import './App.css';

function App() {
    const base = import.meta.env.BASE_URL || '/';

    const user = {
      name: "Igor Colomoyski",
      age: 27,
      bio: "I`m just cool ukrainian guy",
      photo: base + "UserCard.png",
    };

    return (
      <div className="app" style={{
        backgroundImage: `url(${base}background_new.png)`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        minHeight: '100vh',
        backgroundRepeat: 'no-repeat'
      }}>
        <header className="header">
          <div className="Header-box" style={{
            backgroundImage: `url(${base}background_2.png)`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
          }}>
            <div className="left-part">
                <button className="Filters-Button">
                    <img src={base + "list.svg"} alt="" className="filter-icon" />
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
                    <img src={base + "danger.svg"} alt="" className="report-icon" />
                    Report
                </button>
            </div>
          </div>
        </header>
        <div id="main-page" className="page">
          <div className="Main-box">
            <div className="User-full-card">
                <div className="User-photo-card">
                    <img src={base + "UserCard.png"} alt="User-photo" className="Photo-of-User" />
                    <div className="Box-for-text">
                        <h4 className="User-name">Igor Colomoyski, 27</h4>
                        <h5 className="Text-from-User">I`m just cool ukrainian guy</h5>
                    </div>
                </div>
                <div className="Users-music-stats">
                    Lorem ipsum dolor sit amet consectetur adipisicing elit. Ex saepe veniam, molestiae eum magnam sint. Sunt dicta, sapiente maiores voluptate perspiciatis maxime enim praesentium eos ullam consequuntur quisquam vero nesciunt.
                </div>
            </div>
            <div className="side-bar" style={{
              backgroundImage: `url(${base}background_2.png)`,
              backgroundSize: 'cover',
              backgroundPosition: 'center',
            }}>
                <div className="sidebar-buttons">
                    <img src={base + "UserPhoto.png"} alt="User-Photo" className="sidebar-user_photo" />
                    <button className="Like-button">
                        <img src={base + "user-add.svg"} alt="" className="like-icon" />
                    </button>
                    <button className="Chat-button">
                        <img src={base + "chat-icon-png.png"} alt="" className="chat-icon" />
                    </button>
                    <button className="Skip-button">
                        <img src={base + "skip-button.svg"} alt="" className="skip-icon" />
                    </button>
                </div>
            </div>
          </div>
        </div>
        
        <footer className="Choose-page-box">
          <div className="footer-buttons" style={{
            backgroundImage: `url(${base}background_2.png)`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
          }}>
            <button className="Main-page">
                <img src={base + "home.svg"} alt="" />
            </button>
            <button className="Likes-page">
                <img src={base + "heart.svg"} alt="" />
            </button>
            <button className="Chats-page">
                <img src={base + "mail.svg"} alt="" />
            </button>
            <button className="Profile-page">
                <img src={base + "smile.svg"} alt="" />
            </button>
          </div>
        </footer>
      </div>
    )
}

export default App