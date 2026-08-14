# MuseTwinDate

**Dating App for Telegram — find your match by music taste.**

MuseTwinDate is a Telegram Mini App that connects people based on their music preferences. Instead of swiping through random profiles, users discover each other through shared songs, artists, and genres. The main thing is make dating app and then add AI searching for music taste. And after collecting users -> start making premium functions for monetisation.  /// - The main problem at this moment is choosing between two ways : Music as main focus of searching , or musis AI searching it just a one of the function.

*First way: You add your favourite genres , artists , music-names and searching for people with same taste. [This way is more unique, so it has much more perspective as I think]

*Second way: Simple dating app , where a lot of ways to search people and one of them is music taste. 

Built on top of the **MuseTwin** recommendation engine — the same algorithm that finds similar tracks, now finding similar people.

---

## How It Works

1. **User signs in** via Telegram (no password needed).
2. **Selects favorite songs** (in future add Spotify or Yandex.Music import)
3. **The MuseTwin algorithm** analyzes music preferences and creates a taste vector.
4. **Users are shown profiles** with a similarity score based on shared music taste.
5. **Like / Pass** — if both like, it's a match.
6. **Premium users** get advanced filters, unlimited likes, and see who visited them , AI-functions.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI (for AI-services / not sure); GOlang for any other backend |
| **Database** | PostgreSQL or MySQL ( not sure for the moment) |
| **Frontend (Mini App)** | HTML, CSS, JavaScript, React |
| **Telegram Bot** | aiogram (Python) |
| **Recommendation Engine** | MuseTwin (Pandas, Scikit-learn) |
| **Deployment** | Docker, Linux, VPS |

---

License
All Rights Reserved — This project is proprietary. The code is available for portfolio purposes only.

No part of this code may be copied, modified, distributed, or used without explicit written permission from the author.

Copyright (c) 2026 Daniil Kryuchkov

**Author**
Daniil (BankaHooks)
Software Engineer / Product Builder
GitHub: BankaHooks
Telegram: @DanHooksWork
Email: bankahookswork@gmail.com
