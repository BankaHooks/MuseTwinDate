from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard():
    buttons = [
        [InlineKeyboardButton(text="👀 Browse", callback_data="browse")],
        [InlineKeyboardButton(text="❤️ Likes", callback_data="likes")],
        [InlineKeyboardButton(text="💬 Chats", callback_data="chats")],
        [InlineKeyboardButton(text="👤 Profile", callback_data="profile")],
        [InlineKeyboardButton(text="⭐ Premium", callback_data="premium")],
        [InlineKeyboardButton(text="🌐 Open App", web_app={"url": "https://your-domain.com/MuseTwinDate/"})],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def browse_actions_keyboard():
    buttons = [
        [InlineKeyboardButton(text="❤️ Like", callback_data="like"),
         InlineKeyboardButton(text="⏩ Skip", callback_data="skip")],
        [InlineKeyboardButton(text="👤 View Profile", callback_data="view_profile")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def profile_view_keyboard():
    buttons = [
        [InlineKeyboardButton(text="✏️ Edit Name", callback_data="edit_name"),
         InlineKeyboardButton(text="✏️ Edit Age", callback_data="edit_age")],
        [InlineKeyboardButton(text="✏️ Edit City", callback_data="edit_city"),
         InlineKeyboardButton(text="✏️ Edit Genre", callback_data="edit_genre")],
        [InlineKeyboardButton(text="✏️ Edit Bio", callback_data="edit_bio"),
         InlineKeyboardButton(text="🖼️ Change Photo", callback_data="edit_photo")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def genre_keyboard():
    genres = ["Rock", "Pop", "Jazz", "Electronic", "Indie", "Classical", "Hip-Hop", "Country", "Blues", "Metal", "Other"]
    buttons = [[InlineKeyboardButton(text=g, callback_data=f"genre_{g}")] for g in genres]
    buttons.append([InlineKeyboardButton(text="🔙 Cancel", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def report_reason_keyboard():
    reasons = ["Spam", "Inappropriate", "Fake", "Other"]
    buttons = [[InlineKeyboardButton(text=r, callback_data=f"report_{r}")] for r in reasons]
    buttons.append([InlineKeyboardButton(text="🔙 Cancel", callback_data="cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def premium_plans_keyboard():
    buttons = [
        [InlineKeyboardButton(text="1 month – 100 ⭐", callback_data="premium_1")],
        [InlineKeyboardButton(text="3 months – 250 ⭐", callback_data="premium_3")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)