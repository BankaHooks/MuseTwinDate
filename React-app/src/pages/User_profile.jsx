import React , { useState } from 'react';
import { BrowserRouter, Routes, Route, Link} from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import '../styles/User-profile.css'

const User_Profile = () => {
    const base = import.meta.env.BASE_URL || '/';

    const user_info = {
        age : '18',
        gender : 'man',
        city : 'Taganrog',
        bio : '<150 words',
        music_stats : {
            favorite_genre : 'Rock',
            favorite_band : 'Weezer',
            favorite_language : 'English',
            second_genre : 'Metal',
            third_genre : 'Pop', 
            fourth_genre : 'Nu-Metal', /* Just concept of user music-stats*/
        },
        user_pic : 'src_for_img', /* - source to image, or maybe just text and + '.png' */
        topics_interestedIn : ['Coding' , 'Cooking' , 'English', 'Reading' , 'Dogs', 'Video-games'], /* No more then 10 topics per user!*/
        type_of_searching : ['Flirt','Dating','Friendship','Just talking','Dont`t care'],
        vizualization : 'vizualization.png',

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
        <div className="user-profile-grid">
            <div className="user-bio">
                <div className="user-photo">
                    <img src="UserPhoto.png" alt="*" className="user-photo-file" />
                </div>
                <div className="bio">
                    <p className="Bio-text">Russian student. Software engineer. Making useful products for people like this.</p>
                </div>
            </div>
            <div className="user-music-stats">
                <div className="basic-stats">
                    <ul>
                        <li>{ user_info.music_stats.favorite_genre }</li>
                        <li>{user_info.music_stats.second_genre}</li>
                        <li>{user_info.music_stats.third_genre}</li>
                        <li>{user_info.music_stats.fourth_genre}</li>
                    </ul>
                </div>
                <div className="graphic-stats">
                    <img src={user_info.vizualization} alt="#" className='vizualization-pic'/>
                </div>
            </div>

        <Footer />
        </div>
    </div>
    )
};

export default User_Profile;