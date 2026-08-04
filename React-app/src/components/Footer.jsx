function Footer () {
    const base = import.meta.env.BASE_URL || '/';
    return (
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
    )
}

export default Footer;