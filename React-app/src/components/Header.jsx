function Header ({ onFilterClick, onReportClick }) {
    const base = import.meta.env.BASE_URL || '/';
    return (
        <header className="header">
          <div className="Header-box" style={{
            backgroundImage: `url(${base}background_2.png)`,
            backgroundSize: 'cover',
            backgroundPosition: 'center',
          }}>
            <div className="left-part">
                <button 
                className="Filters-Button"
                onClick={onFilterClick}
                >
                    <img src={base + "list.svg"} alt="" className="filter-icon" />
                    Filters
                </button>
            </div>
            <div className="middle-part">
                <h2 className="App-name">
                    MuseTwin
                </h2>            
            </div>
            <div className="right-part">
                <button className="Report-Button" onClick={onReportClick}>
                    <img src={base + "danger.svg"} alt="" className="report-icon" />
                    Report
                </button>
            </div>
          </div>
        </header>
    )
}

export default Header;