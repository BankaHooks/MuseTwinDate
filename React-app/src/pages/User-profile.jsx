import React , { useState } from 'react';
import { BrowserRouter, Routes, Route, Link} from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import '../styles/User-profile.css'

const User_Profile = () => {
    const base = import.meta.env.BASE_URL || '/';

    const user_info = {
        age = '18',
        gender = 'man',
        city = 'Taganrog',
        bio = '<150 words',
        music_statc = {
            'favorite_genre' : 'Rock',
            'favorite_band' : 'Weezer',
            'favorite_language' : 'English',
            'second_genre' : 'Metal',
            'Third_genre' : 'Pop' /* Just concept of user music-stats*/
        },
        user_pic = 'src_for_img',
        topics_interestedIn = ['Coding' , 'Cooking' , 'English', 'Reading' , 'Dogs', 'Video-games'] /* No more then 10 topics per user!*/

    }

    return (
    // <div className="app" style={{
    //     backgroundImage: `url(${base}background_new.png)`,
    //     backgroundSize: 'cover',
    //     backgroundPosition: 'center',
    //     minHeight: '100vh',
    //     backgroundRepeat: 'no-repeat'
    //     }}>
    //         <Header />
        // </div>
        <div className="user-profile-grid">
            <div className="user-bio">
                <div class="user-photo">
                    <img src="UserPhoto.png" alt="*" className="user-photo-file" />
                </div>
                <div className="bio">
                    <p className="Bio-text">Russian student. Software engineer. Making useful products for people like this.</p>
                </div>
            </div>
            <div className="user-music-stats">
                <div className="basic-stats">
                    <p>blablabla</p>
                </div>
                <div className="graphic-stats">
                    <p>cool vizualization</p>
                </div>
            </div>
        </div>
        // <Footer />
    )
};

export default User_Profile;