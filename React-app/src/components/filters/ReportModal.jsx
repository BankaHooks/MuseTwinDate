import React, { useEffect, useState } from 'react';
import Modal from '../common/Modal';
import '../../styles/ReportModal.css';

const ReportModal = ({ isOpen , onClose, onApply}) => {
    const [reason, setReason] = useState('');

    useEffect(() => {
        if (isOpen) {
            setReason('');
        }
    }, [isOpen]);

    const handleSubmit = () => {
        if (reason.trim() === '') return;
        onApply(reason);
        onClose();
    };

    const handleCancel = () => {
        onClose();
    }


    return (
        <Modal isOpen={isOpen} onClose={onClose}>
            <div className='report-modal'>
                <h3>Reason of report</h3>

                <div className='reasons-of-report'>
                    <div className='radio-group'>
                        <label>
                            <input
                            type='radio'
                            name='reason'
                            value='Sexual content'
                            onChange={() => setReason('Sexual content')}
                            ></input>
                            Sexual content
                        </label>
                        <label>
                            <input
                            type='radio'
                            name='reason'
                            value='Prohibited substances'
                            onChange={() => setReason('Prohibited substances')}
                            ></input>
                            Prohibited substances
                        </label>
                        <label>
                            <input
                            type='radio'
                            name='reason'
                            value='Advertising'
                            onChange={() => setReason('Advertising')}
                            ></input>
                            Advertising
                        </label>
                        <label>
                            <input
                            type='radio'
                            name='reason'
                            value='Bullying'
                            onChange={() => setReason('Bullying')}
                            ></input>
                            Bullying
                        </label>
                    </div>
                </div>

                <div className='report-actions'>
                    <button onClick={handleCancel} className='btn-cancel'>Cancel</button>
                    <button onClick={handleSubmit} className='btn-apply'>Apply</button>
                </div>

            </div>
        </Modal>
    );
};

export default ReportModal;