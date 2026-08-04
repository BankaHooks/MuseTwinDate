function UserCard ({ user }) {
    const base = import.meta.env.BASE_URL || '/';
    return (
        <div className="User-full-card">
            <div className="User-photo-card">
                <img src={base + "UserCard.png"} alt="User-photo" className="Photo-of-User" />
                <div className="Box-for-text">
                    <h4 className="User-name">{user.name}, {user.age}</h4>
                    <h5 className="Text-from-User">{user.bio}</h5>
                </div>
            </div>
        </div>
    );
};

export default UserCard;