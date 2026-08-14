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
        bio : 'Russian student. Software engineer. Making useful products for people like this one.',
        music_stats : {
            favorite_genre : 'Rock',  /* You have one favorite genre, artist/band, song, and few liked */
            favorite_band : 'Weezer',
            favorite_song : 'King of the World',
            native_language : 'English',
            liked_genres : ['Metal' , 'Pop' , 'Nu-Metal'], /* Just concept of user music-stats*/
            liked_bands : ['Queen' , 'The Beatles' , 'Megadeth' , 'Oasis', 'ДДТ'],
            liked_songs : ['Pearly' , 'Norwegian woods' , 'Go Away'],   /* I think limit will be about 3 - liked genres , 5 - liked genres and 3 liked songs */
        },
        user_pic : 'src_for_img', /* - source to image, or maybe just text and + '.png' */
        topics_interestedIn : ['Coding' , 'Cooking' , 'English', 'Reading' , 'Dogs', 'Video-games'], /* No more then 10 topics per user!*/
        type_of_searching : 'Flirt' , /* ['Flirt','Dating','Friendship','Just talking','Dont`t care'] */
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
                    <p className="Bio-text"></p>
                    { user_info.age }
                    { user_info.city }
                    { user_info.bio }
                    { user_info.type_of_searching }
                    <div className='Liked-topics'>
                        { user_info.topics_interestedIn }
                    </div>
                </div>
            </div>
            <div className="user-music-stats">
                <div className="basic-stats">
                    <ul>
                        <li>{ user_info.music_stats.favorite_genre }</li>
                        <li>{user_info.music_stats.favorite_band}</li>
                        <li>{user_info.music_stats.favorite_song}</li>
                        <ul>
                            <li>{ user_info.music_stats.liked_genres}</li>
                            <li>{ user_info.music_stats.liked_bands}</li>
                            <li>{ user_info.music_stats.liked_songs}</li>
                        </ul>
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