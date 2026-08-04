import React, { useState } from 'react';
import Header from '../components/Header';
import FilterModal from '../components/filters/FilterModal';
import UserCard from '../components/UserCard';
import UserStats from '../components/UserStats';
import Sidebar from '../components/Sidebar';
import Footer from '../components/Footer';

const Home = () => {
    const base = import.meta.env.BASE_URL || '/';

    const user = {
        name: "Igor Colomoyski",
        age: 27,
        bio: "I`m just cool ukrainian guy",
        photo: base + "UserCard.png",
    };

    // Состояние фильтров
    const [isFilterOpen, setIsFilterOpen] = useState(false);
    const [filters, setFilters] = useState({
        gender: 'everyone',
        ageMin: 18,
        ageMax: 35,
        city: "Taganrog",
    });

    const openFilter = () => setIsFilterOpen(true);
    const closeFilter = () => setIsFilterOpen(false);

    const applyFilters = (newFilters) => {
        setFilters(newFilters);
        setIsFilterOpen(false);
    };

    return (
        <div className="app" style={{
            backgroundImage: `url(${base}background_new.png)`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            minHeight: '100vh',
            backgroundRepeat: 'no-repeat'
        }}>
            <Header onFilterClick={openFilter} />

            <div id="main-page" className="page">
                <div className="Main-box">
                    <UserCard user={user} filters={filters} />
                    <UserStats />
                </div>

                <Sidebar />

            </div>

            <Footer />

            <FilterModal
                isOpen={isFilterOpen}
                onClose={closeFilter}
                onApply={applyFilters}
                initialFilters={filters}
            />
        </div>
    );
};

export default Home;