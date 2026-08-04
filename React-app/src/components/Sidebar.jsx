function Sidebar () {
    const base = import.meta.env.BASE_URL || '/';
    return (
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
    )
}

export default Sidebar;