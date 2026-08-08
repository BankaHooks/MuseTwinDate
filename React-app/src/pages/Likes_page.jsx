import { useState } from 'react';
import Header from '../components/Header';
import Footer from '../components/Footer';
import '../styles/Likes-page.css'

const Likes_Page = () => {
    const base = import.meta.env.BASE_URL || '/';

    const users_likes = {
        name : 'Maria',
        age : '19',
        bio : 'text-test',
        city : 'Saint-Petersburg',
        favorite_genre : 'Rock',
    };

    return (
    <div className="User-style" style={{
        backgroundImage: `url(${base}background_new.png)`,
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        minHeight: '100vh',
        backgroundRepeat: 'no-repeat'
        }}>
        <Header showActions={false} />
        <div className="Likes-page-grid">
            <div className='Likes-cards-row'>
                <div className='user-card'>
                    <div className='bio-from-likes'>
                        <p className='text-from-bio'>{users_likes.name} {users_likes.age} {users_likes.city} </p>
                        <p className='text-from-bio'>{users_likes.bio}</p>
                        <p className='text-from-bio'>{users_likes.favorite_genre}</p>
                    </div>
                    <img src={base + "UserCard.png"} alt="users-card-like" className='users-card-like'/>
                </div>
                <div className='user-card'>
                    <div className='bio-from-likes'>
                        <p className='text-from-bio'>{users_likes.name} {users_likes.age} {users_likes.city} </p>
                        <p className='text-from-bio'>{users_likes.bio}</p>
                        <p className='text-from-bio'>{users_likes.favorite_genre}</p>
                    </div>
                    <img src={base + "UserCard.png"} alt="users-card-like" className='users-card-like'/>
                </div>
                <div className='user-card'>
                    <div className='bio-from-likes'>
                        <p className='text-from-bio'>{users_likes.name} {users_likes.age} {users_likes.city} </p>
                        <p className='text-from-bio'>{users_likes.bio}</p>
                        <p className='text-from-bio'>{users_likes.favorite_genre}</p>
                    </div>
                    <img src={base + "UserCard.png"} alt="users-card-like" className='users-card-like'/>
                </div>
            </div>

            <div className='Likes-cards-row'>
                <div className='user-card'>
                    <div className='bio-from-likes'>
                        <p className='text-from-bio'>{users_likes.name} {users_likes.age} {users_likes.city} </p>
                        <p className='text-from-bio'>{users_likes.bio}</p>
                        <p className='text-from-bio'>{users_likes.favorite_genre}</p>
                    </div>
                    <img src={base + "UserCard.png"} alt="users-card-like" className='users-card-like'/>
                </div>
                <div className='user-card'>
                    <div className='bio-from-likes'>
                        <p className='text-from-bio'>{users_likes.name} {users_likes.age} {users_likes.city} </p>
                        <p className='text-from-bio'>{users_likes.bio}</p>
                        <p className='text-from-bio'>{users_likes.favorite_genre}</p>
                    </div>
                    <img src={base + "UserCard.png"} alt="users-card-like" className='users-card-like'/>
                </div>
                <div className='user-card'>
                    <div className='bio-from-likes'>
                        <p className='text-from-bio'>{users_likes.name} {users_likes.age} {users_likes.city} </p>
                        <p className='text-from-bio'>{users_likes.bio}</p>
                        <p className='text-from-bio'>{users_likes.favorite_genre}</p>
                    </div>
                    <img src={base + "UserCard.png"} alt="users-card-like" className='users-card-like'/>
                </div>
            </div>

            <div className='Likes-cards-row'>
                <div className='user-card'>
                    <div className='bio-from-likes'>
                        <p className='text-from-bio'>{users_likes.name} {users_likes.age} {users_likes.city} </p>
                        <p className='text-from-bio'>{users_likes.bio}</p>
                        <p className='text-from-bio'>{users_likes.favorite_genre}</p>
                    </div>
                    <img src={base + "UserCard.png"} alt="users-card-like" className='users-card-like'/>
                </div>
                <div className='user-card'>
                    <div className='bio-from-likes'>
                        <p className='text-from-bio'>{users_likes.name} {users_likes.age} {users_likes.city} </p>
                        <p className='text-from-bio'>{users_likes.bio}</p>
                        <p className='text-from-bio'>{users_likes.favorite_genre}</p>
                    </div>
                    <img src={base + "UserCard.png"} alt="users-card-like" className='users-card-like'/>
                </div>
                <div className='user-card'>
                    <div className='bio-from-likes'>
                        <p className='text-from-bio'>{users_likes.name} {users_likes.age} {users_likes.city} </p>
                        <p className='text-from-bio'>{users_likes.bio}</p>
                        <p className='text-from-bio'>{users_likes.favorite_genre}</p>
                    </div>
                    <img src={base + "UserCard.png"} alt="users-card-like" className='users-card-like'/>
                </div>
            </div>
        </div>

        <Footer />
        </div>
    );
};
export default Likes_Page;