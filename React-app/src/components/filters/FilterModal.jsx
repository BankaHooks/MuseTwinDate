import React, { useState, useEffect } from 'react';
import Modal from '../common/Modal';
import '../../styles/FilterModal.css';

const FilterModal = ({ isOpen, onClose, onApply, initialFilters}) => {
    const [gender, setGender] = useState(initialFilters.gender);
    const [ageMin, setAgeMin] = useState(initialFilters.ageMin);
    const [ageMax,setAgeMax] = useState(initialFilters.ageMax);
    const [city, setCity] = useState(initialFilters.city);

    useEffect(() => {
        if (isOpen) {
            setGender(initialFilters.gender);
            setAgeMin(initialFilters.ageMin);
            setAgeMax(initialFilters.ageMax);
            setCity(initialFilters.city);
        }
    }, [isOpen, initialFilters]);

    const handleApply = () => {
        onApply({ gender, ageMin, ageMax, city});
    };

    const handleCancel = () => {
        onClose();
    };

    return (
        <Modal isOpen={isOpen} onClose={onClose}>
            <div className='filter-modal'>
                <h3>Filters</h3>

                <div className='filter-group'>
                    <label>Gender</label>
                    <div className='radio-group'>
                        <label>
                            <input 
                            type="radio"
                            name="gender"
                            value="women"
                            checked={gender === "women"}
                            onChange={() => setGender('women')}
                            />
                            Women
                        </label>
                        <label>
                            <input 
                            type="radio"
                            name='gender'
                            value='men'
                            checked={gender === 'men'}
                            onChange={() => setGender("men")}
                            />
                            Men
                        </label>
                        <label>
                            <input 
                            type="radio"
                            name="gender"
                            value="everyone"
                            checked={gender === 'everyone'}
                            onChange={() => setGender('everyone')}
                            />
                            Everyone
                        </label>
                    </div>
                </div>

                <div className='filter-group'>
                    <label>Age: {ageMin} - {ageMax}</label>
                    <div className='range-row'>
                        <input 
                        type="number"
                        value={ageMin}
                        onChange={(e) => setAgeMin(Number(e.target.value))}
                        min="18"
                        max="99"
                         />
                        <span>-</span>
                        <input 
                        type="number"
                        value={ageMax}
                        onChange={(e) =>setAgeMax(Number(e.target.value))}
                        min="18"
                        max="99"
                        />
                    </div>
                </div>

                <div className='filter-group'>
                    <label>City: {city}</label>
                    <input 
                    type="text"
                    name="City"
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                     />
                </div>

                <div className='filter-actions'>
                    <button onClick={handleCancel} className='btn-cancel'>Cancel</button>
                    <button onClick={handleApply} className='btn-apply'>Apply</button>
                </div>
            </div>
        </Modal>
    );
};

export default FilterModal;