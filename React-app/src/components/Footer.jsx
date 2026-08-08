import { useNavigate } from 'react-router-dom';

function Footer () {
    const base = import.meta.env.BASE_URL || '/';
    const navigate = useNavigate();

    const toMainPage = () => navigate('/')
    const toLikesPage = () => navigate('/Likes-page')
    const toChatsPage = () => navigate('/Chats-page')
    const toProfilePage = () => navigate('/User-profile')


    return (
        <footer className="Choose-page-box">
            <div className="footer-buttons" style={{
            backgroundImage: `url(${base}background_2.png)`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
          }}>

                <button className="Main-page" onClick={toMainPage}>
                    <img src={base + "home.svg"} alt="" />
                </button>
                <button className="Likes-page" onClick={toLikesPage}>
                    <img src={base + "heart.svg"} alt="" />
                </button>
                <button className="Chats-page" onClick={toChatsPage}>
                    <img src={base + "mail.svg"} alt="" />
                </button>
                <button className="Profile-page" onClick={toProfilePage}>
                    <img src={base + "smile.svg"} alt="" />
                </button>
          </div>
        </footer>
    )
}

export default Footer;