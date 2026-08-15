def validate_age(age_str: str) -> bool:
    try:
        age = int(age_str)
        return 18 <= age <= 99
    except ValueError:
        return False

def format_user_card(user) -> str:
    text = f"👤 {user.name or 'No name'}\n"
    if user.age:
        text += f"🎂 {user.age} years old\n"
    if user.city:
        text += f"📍 {user.city}\n"
    if user.genre:
        text += f"🎵 {user.genre}\n"
    if user.bio:
        text += f"📝 {user.bio}\n"
    return text