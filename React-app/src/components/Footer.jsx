import { useNavigate } from 'react-router-dom';

function Footer () {
    const base = import.meta.env.BASE_URL || '/';

    const Navigation = () => {
        const navigate = useNavigate();
    }

    const toMainPage = () => {
        navigate('/')
    }

    const toLikesPage = () => {
        navigate('/Likes-page')
    }

    const toChatsPage = () => {
        navigate('/Chats-page')
    }

    const toProfilePage = () => {
        navigate('/User-profile')
    }

    return (
        <footer className="Choose-page-box">
            <div className="footer-buttons" style={{
            backgroundImage: `url(${base}background_2.png)`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
          }}>

            <nav>
                <button className="Main-page" onClick={ toMainPage }>
                    {/* <Link to="/"></Link> */}
                    <img src={base + "home.svg"} alt="" />
                </button>
                <button className="Likes-page" onClick={ toLikesPage }>
                    {/* <Link to="/Likes"></Link> */}
                    <img src={base + "heart.svg"} alt="" />
                </button>
                <button className="Chats-page" onClick={ toChatsPage }>
                    {/* <Link to="/Chats-page"></Link> */}
                    <img src={base + "mail.svg"} alt="" />
                </button>
                <button className="Profile-page" onClick={ toProfilePage }>
                    {/* <Link to="/User-Profile"></Link> */}
                    <img src={base + "smile.svg"} alt="" />
                </button>
            </nav>

            {/* Idintification Routes
            <Routes>
                <Route path='/' element={<Home />} />
                <Route path='/Likes' element={<Likes-page />} />
                <Route path='/Chats-page' element={<Chats-page />} />
                <Route path='User-Profile' element={<User-profile />} />

                <Route path="*" element={<NotFound />} />

            </Routes> */}

          </div>
        </footer>
    )
}

export default Footer;