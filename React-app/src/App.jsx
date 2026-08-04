import './App.css';
import Header from './components/Header';
import UserCard from './components/UserCard';
import UserStats from './components/UserStats';
import Sidebar from './components/Sidebar';
import Footer from './components/Footer';


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
        <Header />
        <div id="main-page" className="page">
          <div className="Main-box">
            <UserCard user = {user}/>
            <UserStats />
          </div>
          <Sidebar />
        </div>
        <Footer />
      </div>
    )
}

export default App