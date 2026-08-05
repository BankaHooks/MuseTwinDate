import React, { useState } from 'react';
import Header from '../components/Header';
import FilterModal from '../components/filters/FilterModal';
import UserCard from '../components/UserCard';
import UserStats from '../components/UserStats';
import Sidebar from '../components/Sidebar';
import Footer from '../components/Footer';
import ReportModal from '../components/filters/ReportModal';

const Home = () => {
    const base = import.meta.env.BASE_URL || '/';

    const user = {
        name: "Igor Colomoyski",
        age: 27,
        bio: "I`m just cool ukrainian guy",
        photo: base + "UserCard.png",
    };

    const [isFilterOpen, setIsFilterOpen] = useState(false);
    const [filters, setFilters] = useState({
        gender: 'everyone',
        ageMin: 18,
        ageMax: 35,
        city: "Taganrog",
    });

    const openFilter = () => {
        console.log('OPEN_FILTER');
        setIsFilterOpen(true);
    };
    const closeFilter = () => setIsFilterOpen(false);

    const applyFilters = (newFilters) => {
        setFilters(newFilters);
        setIsFilterOpen(false);
    };

    const [isReportOpen, setIsReportOpen] = useState(false);

    const openReport = () => {
        console.log('OPEN_REPORT');
        setIsReportOpen(true);
    };
    const closeReport = () => setIsReportOpen(false);

    const sendReport = (reason) => {
        console.log('Report reason' , reason)
        //Send to server - later
        closeReport();
    };


    return (
        <div className="app" style={{
            backgroundImage: `url(${base}background_new.png)`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
            minHeight: '100vh',
            backgroundRepeat: 'no-repeat'
        }}>
            <Header onFilterClick={openFilter} onReportClick={openReport} />
            

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

            <ReportModal
                isOpen={isReportOpen}
                onClose={closeReport}
                onApply={sendReport}
            />
        </div>
    );
};

export default Home;