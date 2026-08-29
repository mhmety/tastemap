"""TasteMap Database Seed / Initial Data Population Script.

Populates the PostgreSQL database with realistic sample restaurants,
curated categorized menu items, admin & test user accounts, reviews,
Google reviews, and favorites.

Usage:
    python scripts/seed.py
    python scripts/seed.py --reset    (Drops seed data before re-inserting)
    python scripts/seed.py --dry-run  (Displays what would be inserted without committing)
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path
from typing import Any

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Safe fallback for DATABASE_URL if run locally without .env set
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://tastemap:tastemap@localhost:5432/tastemap",
)

from sqlalchemy import delete, select  # noqa: E402
from sqlalchemy.exc import SQLAlchemyError  # noqa: E402

from app.core.security import hash_password  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.favorite import Favorite  # noqa: E402
from app.models.google_review import GoogleReview  # noqa: E402
from app.models.menu_item import MenuItem  # noqa: E402
from app.models.restaurant import Restaurant  # noqa: E402
from app.models.review import Review  # noqa: E402
from app.models.user import User  # noqa: E402

# ==============================================================================
# SAMPLE DATA DEFINITIONS
# ==============================================================================

SEED_USERS: list[dict[str, Any]] = [
    {
        "username": "admin",
        "email": "admin@tastemap.com",
        "password": "AdminPassword123!",
        "is_admin": True,
        "is_active": True,
    },
    {
        "username": "gurme_ahmet",
        "email": "ahmet.gurme@example.com",
        "password": "UserPassword123!",
        "is_admin": False,
        "is_active": True,
    },
    {
        "username": "zeynep_lezzet",
        "email": "zeynep.lezzet@example.com",
        "password": "UserPassword123!",
        "is_admin": False,
        "is_active": True,
    },
    {
        "username": "can_foodie",
        "email": "can.foodie@example.com",
        "password": "UserPassword123!",
        "is_admin": False,
        "is_active": True,
    },
    {
        "username": "selin_tastemap",
        "email": "selin.tastemap@example.com",
        "password": "UserPassword123!",
        "is_admin": False,
        "is_active": True,
    },
]

SEED_RESTAURANTS: list[dict[str, Any]] = [
    {
        "name": "Gaziantep Kebap & Lahmacun Salonu",
        "city": "İstanbul",
        "district": "Kadıköy",
        "latitude": 40.9912,
        "longitude": 29.0275,
        "website": "https://gaziantepkebap-kadikoy.example.com",
        "phone": "+90 216 345 67 89",
        "description": "Geleneksel zırh kıymasıyla hazırlanan kebaplar, çıtır taş fırın lahmacun ve otantik Antep baklavası.",
        "category": "kebab shop",
        "price_level": "₺₺",
        "rating": 4.8,
        "review_count": 342,
        "opening_hours": "Pazartesi - Pazar: 11:00 - 23:30",
        "operating_hours": {
            "monday": "11:00 AM – 11:30 PM",
            "tuesday": "11:00 AM – 11:30 PM",
            "wednesday": "11:00 AM – 11:30 PM",
            "thursday": "11:00 AM – 11:30 PM",
            "friday": "11:00 AM – 11:30 PM",
            "saturday": "11:00 AM – 11:30 PM",
            "sunday": "11:00 AM – 11:00 PM",
        },
        "thumbnail": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=800&q=80",
        "menu_items": [
            {
                "name": "Fıstıklı Zırh Kebabı",
                "price": 440.00,
                "category": "kebabs",
                "description": "Zırhta çekilmiş özel kuzu kıyması ve taze Gaziantep boz Antep fıstığı, lavaş ve köz sebzelerle.",
            },
            {
                "name": "Ali Nazik Kebabı",
                "price": 470.00,
                "category": "kebabs",
                "description": "Sarımsaklı süzme yoğurtlu köz patlıcan yatağında tereyağlı yumuşacık marine kuzu lokum parçaları.",
            },
            {
                "name": "Beyti Sarma Kebap",
                "price": 460.00,
                "category": "kebabs",
                "description": "İnce lavaşa sarılmış ızgara kıyma köfteler, domates sos, kızgın tereyağı ve süzme yoğurt.",
            },
            {
                "name": "Taş Fırın Çıtır Lahmacun",
                "price": 120.00,
                "category": "lahmacun",
                "description": "Odun ateşinde pişmiş ince çıtır hamur, zırh kıyması, maydanoz ve limon eşliğinde.",
            },
            {
                "name": "Közde Patlıcanlı Kebap",
                "price": 430.00,
                "category": "kebabs",
                "description": "Köz patlıcan dilimleri arasına dizilmiş kuzu zırh kıyması.",
            },
            {
                "name": "Süzme Mercimek Çorbası",
                "price": 110.00,
                "category": "soups",
                "description": "Kıtır tereyağlı ekmek ve limon dilimi ile servis edilen geleneksel süzme mercimek.",
            },
            {
                "name": "Gavurdağı Salatası",
                "price": 160.00,
                "category": "salads",
                "description": "Küp doğranmış domates, salatalık, taze ceviz içi, nar ekşisi ve sızma zeytinyağı.",
            },
            {
                "name": "Havuç Dilim Baklava (Kayıklı)",
                "price": 260.00,
                "category": "desserts",
                "description": "Bol Antep fıstıklı çıtır havuç dilim baklava, isteğe göre Maraş kesme dondurması ile.",
            },
            {
                "name": "Köpüklü Yayık Ayranı",
                "price": 50.00,
                "category": "drinks",
                "description": "Taze ev yapımı bol köpüklü yayık ayranı.",
            },
            {
                "name": "Adana Şalgam Suyu (Acılı/Acısız)",
                "price": 55.00,
                "category": "drinks",
                "description": "Geleneksel fermantasyon yöntemiyle üretilmiş organik şalgam suyu.",
            },
        ],
    },
    {
        "name": "Artisan Burger Lab & Craft Fries",
        "city": "İstanbul",
        "district": "Beşiktaş",
        "latitude": 41.0428,
        "longitude": 29.0078,
        "website": "https://artisanburgerlab.example.com",
        "phone": "+90 212 236 12 34",
        "description": "Özel dinlendirilmiş dana etinden smash burgerler, brioche ekmekler ve trüflü el yapımı patatesler.",
        "category": "hamburger restaurant",
        "price_level": "₺₺",
        "rating": 4.7,
        "review_count": 210,
        "opening_hours": "Pazartesi - Pazar: 12:00 - 00:00",
        "operating_hours": {
            "monday": "12:00 PM – 12:00 AM",
            "tuesday": "12:00 PM – 12:00 AM",
            "wednesday": "12:00 PM – 12:00 AM",
            "thursday": "12:00 PM – 12:00 AM",
            "friday": "12:00 PM – 01:00 AM",
            "saturday": "12:00 PM – 01:00 AM",
            "sunday": "12:00 PM – 11:30 PM",
        },
        "thumbnail": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=800&q=80",
        "menu_items": [
            {
                "name": "Truffle Mushroom Angus Burger",
                "price": 395.00,
                "category": "burgers",
                "description": "180gr dinlendirilmiş dana köfte, sote istiridye mantarı, trüflü mayonez, karamelize soğan ve eritilmiş cheddar peyniri.",
            },
            {
                "name": "Double Smash Bacon Burger",
                "price": 430.00,
                "category": "burgers",
                "description": "2x100gr dana smash köfte, çıtır dana füme bacon, çift cheddar, ev yapımı burger sosu ve tereyağlı brioche ekmeği.",
            },
            {
                "name": "Crispy Buttermilk Chicken Burger",
                "price": 320.00,
                "category": "burgers",
                "description": "Ayran marinasyonlu çıtır panelenmiş tavuk göğsü, mor lahana coleslaw salatası ve acılı ballı sriracha sos.",
            },
            {
                "name": "Smoked BBQ Pulled Beef Burger",
                "price": 410.00,
                "category": "burgers",
                "description": "8 saat ağır ateşte pişmiş tiftik dana eti, ev yapımı tütsülenmiş barbekü sos ve çıtır soğan halkaları.",
            },
            {
                "name": "Trüflü & Parmesanlı Patates Kızartması",
                "price": 180.00,
                "category": "sides",
                "description": "Taze baharatlı el kesimi patates kızartması, saf trüf yağı ve rendelenmiş Grana Padano parmesan.",
            },
            {
                "name": "Çıtır Mozzarella Sticks (6 Adet)",
                "price": 165.00,
                "category": "starters",
                "description": "Baharatlı ekmek kırıntısıyla kaplanmış eriyen mozzarella peynir çubukları, tatlı-acı dip sos ile.",
            },
            {
                "name": "Ev Yapımı Çilekli Fesleğenli Limonata",
                "price": 95.00,
                "category": "drinks",
                "description": "Taze sıkılmış limon suyu, ezilmiş dağ çileği ve taze fesleğen yaprakları.",
            },
            {
                "name": "Lotus Biscoff Cheesecake",
                "price": 200.00,
                "category": "desserts",
                "description": "Fırınlanmış kremsi New York usulü cheesecake, bol Lotus kreması ve bisküvi kıtırı ile.",
            },
        ],
    },
    {
        "name": "Trattoria Bella Napoli",
        "city": "Ankara",
        "district": "Çankaya",
        "latitude": 39.8975,
        "longitude": 32.8624,
        "website": "https://bellanapoli-ankara.example.com",
        "phone": "+90 312 440 88 99",
        "description": "Napoli usulü taş fırın pizzalar, taze el yapımı makarnalar ve İtalyan tatlıları.",
        "category": "pizzeria",
        "price_level": "₺₺₺",
        "rating": 4.9,
        "review_count": 265,
        "opening_hours": "Salı - Pazar: 12:30 - 23:00 (Pazartesi Kapalı)",
        "operating_hours": {
            "monday": "Closed",
            "tuesday": "12:30 PM – 11:00 PM",
            "wednesday": "12:30 PM – 11:00 PM",
            "thursday": "12:30 PM – 11:00 PM",
            "friday": "12:30 PM – 11:30 PM",
            "saturday": "12:30 PM – 11:30 PM",
            "sunday": "12:30 PM – 10:30 PM",
        },
        "thumbnail": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=800&q=80",
        "menu_items": [
            {
                "name": "Pizza Margherita Verace D.O.P.",
                "price": 350.00,
                "category": "pizza",
                "description": "San Marzano domates sosu, manda mozzarella peyniri, taze fesleğen ve sızma zeytinyağı.",
            },
            {
                "name": "Pizza Quattro Formaggi",
                "price": 420.00,
                "category": "pizza",
                "description": "Fior di latte mozzarella, gorgonzola, scamorza ve rendelenmiş parmesan peyniri.",
            },
            {
                "name": "Pizza Tartufata con Funghi",
                "price": 480.00,
                "category": "pizza",
                "description": "Siyah trüf kreması, yabani kestane mantarı, mozzarella ve taze kekik yaprakları.",
            },
            {
                "name": "Fettuccine al Tartufo e Funghi",
                "price": 410.00,
                "category": "pasta",
                "description": "El açımı taze fettuccine makarna, yabani mantar sosu, trüf ezmesi ve parmesan.",
            },
            {
                "name": "Gnocchi al Pesto Genovese",
                "price": 370.00,
                "category": "pasta",
                "description": "Ev yapımı patates gnocchi, taze fesleğenli fıstıklı pesto sos ve stracciatella peyniri.",
            },
            {
                "name": "Burrata Pugliese Caprese",
                "price": 310.00,
                "category": "starters",
                "description": "Taze manda burrata peyniri, fırınlanmış renkli salkım domatesler, roka ve balsamik glaze.",
            },
            {
                "name": "Geleneksel Espresso Tiramisu",
                "price": 220.00,
                "category": "desserts",
                "description": "İtalyan Savoiardi bisküvisi, taze espresso ve mascarpone kremasıyla hazırlanan orijinal tarif.",
            },
            {
                "name": "San Pellegrino Aranciata Rossa",
                "price": 90.00,
                "category": "drinks",
                "description": "200ml İtalyan kan portakallı maden suyu.",
            },
        ],
    },
    {
        "name": "Ege Balıkçısı & Meze Evi",
        "city": "İzmir",
        "district": "Alsancak",
        "latitude": 38.4382,
        "longitude": 27.1438,
        "website": "https://egebalikcisi-izmir.example.com",
        "phone": "+90 232 464 55 66",
        "description": "Günlük taze Ege balıkları, zeytinyağlı sıcak ve soğuk mezeler, deniz kokan ferah bahçe.",
        "category": "seafood restaurant",
        "price_level": "₺₺₺",
        "rating": 4.8,
        "review_count": 318,
        "opening_hours": "Pazartesi - Pazar: 13:00 - 00:30",
        "operating_hours": {
            "monday": "01:00 PM – 12:30 AM",
            "tuesday": "01:00 PM – 12:30 AM",
            "wednesday": "01:00 PM – 12:30 AM",
            "thursday": "01:00 PM – 12:30 AM",
            "friday": "01:00 PM – 01:00 AM",
            "saturday": "01:00 PM – 01:00 AM",
            "sunday": "01:00 PM – 12:00 AM",
        },
        "thumbnail": "https://images.unsplash.com/photo-1534422298391-e4f8c172dddb?w=800&q=80",
        "menu_items": [
            {
                "name": "Izgara Ege Levreği Fileto",
                "price": 540.00,
                "category": "mains",
                "description": "Kömür ızgarada pişirilmiş taze levrek filetosu, roka salatası ve fırınlanmış bebek patates eşliğinde.",
            },
            {
                "name": "Tereyağlı Güveçte Jumbo Karides",
                "price": 460.00,
                "category": "starters",
                "description": "Döküm güveçte sarımsak, arpacık soğan, domates ve acı pul biber ile pişen jumbo karidesler.",
            },
            {
                "name": "Çıtır Ege Kalamar Tava & Tarator",
                "price": 410.00,
                "category": "starters",
                "description": "Altın sarısı çıtır taze kalamar halkaları, cevizli sarımsaklı süzme tarator sos ile.",
            },
            {
                "name": "Zeytinyağlı Deniz Börülcesi & Girit Ezmesi",
                "price": 180.00,
                "category": "appetizers",
                "description": "Sarımsaklı limonlu deniz börülcesi ve Antep fıstıklı ezme keçi peyniri tabağı.",
            },
            {
                "name": "Balık Çorbası (Günün Taze Balığından)",
                "price": 160.00,
                "category": "soups",
                "description": "Taze balık suyu, kereviz sapı, havuç ve limon terbiyesi ile hazırlanan nefis çorba.",
            },
            {
                "name": "Fırında Sıcak Tahin Helvası",
                "price": 175.00,
                "category": "desserts",
                "description": "Toprak güveçte fırınlanmış cevizli ve limon kabuğu rendeli sıcak tahin helvası.",
            },
        ],
    },
    {
        "name": "Coffee Craft & Artisan Bakery",
        "city": "Ankara",
        "district": "Çankaya",
        "latitude": 39.9048,
        "longitude": 32.8601,
        "website": "https://coffeecraft-ankara.example.com",
        "phone": "+90 312 427 10 20",
        "description": "Nitelikli 3. nesil kahveler, taze kavrulmuş çekirdekler, el yapımı kruvasan ve San Sebastian.",
        "category": "coffee shop",
        "price_level": "₺",
        "rating": 4.6,
        "review_count": 175,
        "opening_hours": "Pazartesi - Pazar: 08:30 - 23:00",
        "operating_hours": {
            "monday": "08:30 AM – 11:00 PM",
            "tuesday": "08:30 AM – 11:00 PM",
            "wednesday": "08:30 AM – 11:00 PM",
            "thursday": "08:30 AM – 11:00 PM",
            "friday": "08:30 AM – 11:30 PM",
            "saturday": "09:00 AM – 11:30 PM",
            "sunday": "09:00 AM – 10:30 PM",
        },
        "thumbnail": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=800&q=80",
        "menu_items": [
            {
                "name": "Flat White (Double Shot)",
                "price": 115.00,
                "category": "hot drinks",
                "description": "Çift shot espresso ve ipeksi mikro köpüklü sıcak süt.",
            },
            {
                "name": "Iced Salted Caramel Latte",
                "price": 140.00,
                "category": "cold drinks",
                "description": "Espresso, soğuk süt, ev yapımı tuzlu karamel sos ve buz.",
            },
            {
                "name": "V60 Filtre Kahve (Etiyopya Yirgacheffe)",
                "price": 130.00,
                "category": "hot drinks",
                "description": "Çiçeksi ve bergamot aromalı taze çekilmiş single origin filtre kahve.",
            },
            {
                "name": "Cold Brew 18h Reserve",
                "price": 135.00,
                "category": "cold drinks",
                "description": "18 saat boyunca soğuk suyla demlenen düşük asiditeli pürüzsüz kahve.",
            },
            {
                "name": "Akışkan San Sebastian Cheesecake",
                "price": 205.00,
                "category": "desserts",
                "description": "Karamelize üst yüzeyli, içi yumuşak kremsi İspanyol cheesecake, eritilmiş Belçika çikolatası ile.",
            },
            {
                "name": "Füme Hindi & Avokadolu Kruvasan",
                "price": 190.00,
                "category": "sandwiches",
                "description": "Fransız tereyağlı çıtır kruvasan içinde füme hindi, labne, avokado dilimleri ve taze roka.",
            },
            {
                "name": "Taze Bademli Kruvasan",
                "price": 145.00,
                "category": "desserts",
                "description": "Badem kreması dolgulu ve kavrulmuş file badem kaplı çıtır kruvasan.",
            },
        ],
    },
    {
        "name": "Yeşil Vadi Ev Yemekleri & Çorba Salonu",
        "city": "Kırıkkale",
        "district": "Merkez",
        "latitude": 39.8453,
        "longitude": 33.5064,
        "website": "https://yesilvadi-kirikkale.example.com",
        "phone": "+90 318 224 45 56",
        "description": "Geleneksel Türk tencere yemekleri, tereyağlı İspir kuru fasulyesi ve 24 saat taze çorba çeşitleri.",
        "category": "turkish restaurant",
        "price_level": "₺",
        "rating": 4.7,
        "review_count": 128,
        "opening_hours": "7/24 Açık",
        "operating_hours": {
            "monday": "Open 24 hours",
            "tuesday": "Open 24 hours",
            "wednesday": "Open 24 hours",
            "thursday": "Open 24 hours",
            "friday": "Open 24 hours",
            "saturday": "Open 24 hours",
            "sunday": "Open 24 hours",
        },
        "thumbnail": "https://images.unsplash.com/photo-1544025162-d76694265947?w=800&q=80",
        "menu_items": [
            {
                "name": "Kırıkkale Usulü Kelle Paça Çorbası",
                "price": 185.00,
                "category": "soups",
                "description": "Özel sarımsaklı sirkeli terbiye ve kızgın tereyağı ile servis edilen kuzu kelle paça.",
            },
            {
                "name": "Kuzu Etli İspir Kuru Fasulye & Pilav",
                "price": 195.00,
                "category": "mains",
                "description": "Toprak güveçte ağır ateşte pişirilmiş İspir fasulyesi, tereyağlı şehriyeli pirinç pilavı ve turşu.",
            },
            {
                "name": "Hünkar Beğendi Kebap",
                "price": 330.00,
                "category": "mains",
                "description": "Közlenmiş patlıcanlı kaşarlı beğendi yatağında lokum gibi kuzu tas kebabı.",
            },
            {
                "name": "Izgara Anne Köftesi & Püre",
                "price": 270.00,
                "category": "mains",
                "description": "Geleneksel el yapımı ızgara anne köftesi, tereyağlı patates püresi ve köz biber.",
            },
            {
                "name": "Fırında Sütlaç",
                "price": 115.00,
                "category": "desserts",
                "description": "Üzeri nar gibi fırınlanmış pirinçli köy sütlacı, bol fındık içi ile.",
            },
            {
                "name": "Geleneksel Şıra & Yayık Ayranı",
                "price": 45.00,
                "category": "drinks",
                "description": "Taze mayalanmış doğal yayık ayranı.",
            },
        ],
    },
]

SEED_REVIEWS: list[dict[str, Any]] = [
    {
        "user_username": "gurme_ahmet",
        "restaurant_name": "Gaziantep Kebap & Lahmacun Salonu",
        "rating": 5,
        "comment": "Fıstıklı kebabı olağanüstüydü! Zırh kıymasının lezzeti ve Antep fıstığının tazeliği hemen fark ediliyor. Lahmacunları da incecik ve çok çıtır.",
    },
    {
        "user_username": "zeynep_lezzet",
        "restaurant_name": "Trattoria Bella Napoli",
        "rating": 5,
        "comment": "Ankara'da yediğim en otantik Napoli pizzası! Hamurun mayalanması ve San Marzano domates sosunun lezzeti tam İtalya havası veriyor.",
    },
    {
        "user_username": "can_foodie",
        "restaurant_name": "Artisan Burger Lab & Craft Fries",
        "rating": 5,
        "comment": "Double Smash Burger tam bir lezzet patlaması. Ekmeğin yumuşaklığı ve trüflü patatesin çıtırlığı mükemmeldi. Kesinlikle tavsiye ederim.",
    },
    {
        "user_username": "selin_tastemap",
        "restaurant_name": "Coffee Craft & Artisan Bakery",
        "rating": 5,
        "comment": "San Sebastian cheesecake akışkanlığı tam kıvamındaydı. Yanına aldığım V60 Etiyopya kahvesinin aroması harikaydı, atmosfer çok keyifli.",
    },
    {
        "user_username": "gurme_ahmet",
        "restaurant_name": "Ege Balıkçısı & Meze Evi",
        "rating": 5,
        "comment": "Levrek ızgara tam kararında pişirilmişti, içi sulu kalmıştı. Sıcak güveç karides ve deniz börülcesi çok başarılıydı.",
    },
    {
        "user_username": "zeynep_lezzet",
        "restaurant_name": "Yeşil Vadi Ev Yemekleri & Çorba Salonu",
        "rating": 4,
        "comment": "Kelle paça çorbası çok şifalı ve lezzetli. İspir kuru fasulyesi de tereyağlı pilavla harika gidiyor.",
    },
]

SEED_FAVORITES: list[dict[str, str]] = [
    {"user_username": "gurme_ahmet", "restaurant_name": "Gaziantep Kebap & Lahmacun Salonu"},
    {"user_username": "gurme_ahmet", "restaurant_name": "Ege Balıkçısı & Meze Evi"},
    {"user_username": "zeynep_lezzet", "restaurant_name": "Trattoria Bella Napoli"},
    {"user_username": "can_foodie", "restaurant_name": "Artisan Burger Lab & Craft Fries"},
    {"user_username": "selin_tastemap", "restaurant_name": "Coffee Craft & Artisan Bakery"},
]


# ==============================================================================
# SEED EXECUTION ENGINE
# ==============================================================================


def _compute_review_hash(restaurant_id: str, author_name: str, review_text: str) -> str:
    """Generate SHA256 hash to prevent duplicate Google reviews."""
    raw = f"{restaurant_id}|{author_name}|{review_text}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def seed_database(reset: bool = False, dry_run: bool = False) -> dict[str, int]:
    """Execute the database seed process.
    
    Args:
        reset: If True, deletes existing seed data before re-inserting.
        dry_run: If True, runs without committing changes to DB.
        
    Returns:
        Summary statistics dictionary.
    """
    stats = {
        "users_created": 0,
        "users_existing": 0,
        "restaurants_created": 0,
        "restaurants_existing": 0,
        "menu_items_created": 0,
        "reviews_created": 0,
        "google_reviews_created": 0,
        "favorites_created": 0,
    }

    with SessionLocal() as db:
        try:
            print("=" * 70)
            print("🚀 TasteMap Database Seeder")
            print("=" * 70)
            if dry_run:
                print("⚠️  DRY RUN MODE: No changes will be written to the database.\n")
            elif reset:
                print("🧹 RESET MODE: Cleaning previous seed entries before seeding...\n")

            # ------------------------------------------------------------------
            # 1. OPTIONAL RESET
            # ------------------------------------------------------------------
            if reset and not dry_run:
                restaurant_names = [r["name"] for r in SEED_RESTAURANTS]
                db.execute(
                    delete(Restaurant).where(Restaurant.name.in_(restaurant_names))
                )
                user_usernames = [u["username"] for u in SEED_USERS]
                db.execute(
                    delete(User).where(User.username.in_(user_usernames))
                )
                db.flush()
                print("✅ Cleaned existing seed restaurants and test users.")

            # ------------------------------------------------------------------
            # 2. SEED USERS
            # ------------------------------------------------------------------
            print("\n👤 Seeding Users...")
            user_map: dict[str, User] = {}

            for u_data in SEED_USERS:
                stmt = select(User).where(User.username == u_data["username"])
                existing_user = db.execute(stmt).scalar_one_or_none()

                if existing_user:
                    user_map[u_data["username"]] = existing_user
                    stats["users_existing"] += 1
                    print(f"  • [Skip] User '{u_data['username']}' already exists.")
                else:
                    new_user = User(
                        username=u_data["username"],
                        email=u_data["email"],
                        hashed_password=hash_password(u_data["password"]),
                        is_admin=u_data.get("is_admin", False),
                        is_active=u_data.get("is_active", True),
                    )
                    if not dry_run:
                        db.add(new_user)
                        db.flush()
                        user_map[u_data["username"]] = new_user
                    stats["users_created"] += 1
                    print(f"  • [Created] User '{u_data['username']}' ({u_data['email']})")

            # ------------------------------------------------------------------
            # 3. SEED RESTAURANTS & MENU ITEMS
            # ------------------------------------------------------------------
            print("\n🍽️  Seeding Restaurants & Menu Items...")
            restaurant_map: dict[str, Restaurant] = {}

            for r_data in SEED_RESTAURANTS:
                stmt = select(Restaurant).where(
                    Restaurant.name == r_data["name"],
                    Restaurant.city == r_data["city"],
                )
                existing_r = db.execute(stmt).scalar_one_or_none()

                if existing_r:
                    restaurant = existing_r
                    restaurant_map[r_data["name"]] = restaurant
                    stats["restaurants_existing"] += 1
                    print(f"  • [Exists] Restaurant '{r_data['name']}' ({r_data['city']}/{r_data['district']})")
                else:
                    restaurant = Restaurant(
                        name=r_data["name"],
                        city=r_data["city"],
                        district=r_data["district"],
                        latitude=r_data.get("latitude"),
                        longitude=r_data.get("longitude"),
                        website=r_data.get("website"),
                        phone=r_data.get("phone"),
                        description=r_data.get("description"),
                        category=r_data.get("category"),
                        price_level=r_data.get("price_level"),
                        rating=r_data.get("rating"),
                        review_count=r_data.get("review_count"),
                        opening_hours=r_data.get("opening_hours"),
                        operating_hours=r_data.get("operating_hours"),
                        thumbnail=r_data.get("thumbnail"),
                    )
                    if not dry_run:
                        db.add(restaurant)
                        db.flush()
                        restaurant_map[r_data["name"]] = restaurant
                    stats["restaurants_created"] += 1
                    print(f"  • [Created] Restaurant '{r_data['name']}' ({r_data['city']}/{r_data['district']})")

                # Insert Menu Items for this restaurant
                items_data = r_data.get("menu_items", [])
                if restaurant and not dry_run:
                    # Check existing item names to prevent duplicate insertion
                    existing_items_stmt = select(MenuItem.name).where(
                        MenuItem.restaurant_id == restaurant.id
                    )
                    existing_names = set(db.execute(existing_items_stmt).scalars().all())

                    new_items: list[MenuItem] = []
                    for item in items_data:
                        if item["name"] not in existing_names:
                            new_items.append(
                                MenuItem(
                                    restaurant_id=restaurant.id,
                                    name=item["name"],
                                    price=item["price"],
                                    category=item.get("category", "Ana Yemekler"),
                                    description=item.get("description"),
                                )
                            )
                    if new_items:
                        db.add_all(new_items)
                        db.flush()
                        stats["menu_items_created"] += len(new_items)
                        print(f"    ↳ Added {len(new_items)} menu items.")
                elif dry_run:
                    stats["menu_items_created"] += len(items_data)
                    print(f"    ↳ Would add {len(items_data)} menu items.")

            # ------------------------------------------------------------------
            # 4. SEED REVIEWS & GOOGLE REVIEWS
            # ------------------------------------------------------------------
            print("\n⭐ Seeding Reviews & Ratings...")
            if not dry_run:
                for rev in SEED_REVIEWS:
                    user = user_map.get(rev["user_username"])
                    rest = restaurant_map.get(rev["restaurant_name"])
                    if not user or not rest:
                        continue

                    # Check unique review per (user_id, restaurant_id)
                    stmt = select(Review).where(
                        Review.user_id == user.id,
                        Review.restaurant_id == rest.id,
                    )
                    existing_rev = db.execute(stmt).scalar_one_or_none()
                    if not existing_rev:
                        new_rev = Review(
                            user_id=user.id,
                            restaurant_id=rest.id,
                            rating=rev["rating"],
                            comment=rev.get("comment"),
                        )
                        db.add(new_rev)
                        stats["reviews_created"] += 1
                        print(f"  • Review by @{user.username} for '{rest.name}' (Rating: {rev['rating']}/5)")

                # Also insert high-quality Google Reviews for realism
                for r_name, rest in restaurant_map.items():
                    sample_google_reviews = [
                        {
                            "author_name": "Mehmet Yılmaz",
                            "rating": 5,
                            "review_text": "Servis hızı, personelin ilgisi ve yemeklerin lezzeti gerçekten kusursuzdu. Herkese tavsiye ederim.",
                            "review_date": "2 hafta önce",
                        },
                        {
                            "author_name": "Elif Demir",
                            "rating": 5,
                            "review_text": "Menüdeki çeşitlilik ve ürünlerin sunumu harikaydı. Fiyat/performans açısından çok başarılı.",
                            "review_date": "1 ay önce",
                        },
                    ]
                    for g_rev in sample_google_reviews:
                        r_hash = _compute_review_hash(str(rest.id), g_rev["author_name"], g_rev["review_text"])
                        g_stmt = select(GoogleReview).where(GoogleReview.review_hash == r_hash)
                        if not db.execute(g_stmt).scalar_one_or_none():
                            new_g = GoogleReview(
                                restaurant_id=rest.id,
                                author_name=g_rev["author_name"],
                                rating=g_rev["rating"],
                                review_text=g_rev["review_text"],
                                review_date=g_rev["review_date"],
                                review_hash=r_hash,
                                raw_json={"source": "seed", **g_rev},
                            )
                            db.add(new_g)
                            stats["google_reviews_created"] += 1
                db.flush()

            # ------------------------------------------------------------------
            # 5. SEED FAVORITES
            # ------------------------------------------------------------------
            print("\n❤️  Seeding Favorites...")
            if not dry_run:
                for fav in SEED_FAVORITES:
                    user = user_map.get(fav["user_username"])
                    rest = restaurant_map.get(fav["restaurant_name"])
                    if not user or not rest:
                        continue

                    stmt = select(Favorite).where(
                        Favorite.user_id == user.id,
                        Favorite.restaurant_id == rest.id,
                    )
                    if not db.execute(stmt).scalar_one_or_none():
                        new_fav = Favorite(user_id=user.id, restaurant_id=rest.id)
                        db.add(new_fav)
                        stats["favorites_created"] += 1
                        print(f"  • Favorited '{rest.name}' for @{user.username}")

            # ------------------------------------------------------------------
            # COMMIT TRANSACTION
            # ------------------------------------------------------------------
            if not dry_run:
                db.commit()
                print("\n🎉 Seed data successfully committed to database!")
            else:
                db.rollback()
                print("\n✨ Dry run complete. No data was saved.")

        except SQLAlchemyError as exc:
            db.rollback()
            print(f"\n❌ Error during database seeding: {exc}")
            raise

    # ------------------------------------------------------------------
    # SUMMARY & LOGIN CREDENTIALS
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("📊 SEED SUMMARY REPORT")
    print("=" * 70)
    print(f"• Users created            : {stats['users_created']} (Existing: {stats['users_existing']})")
    print(f"• Restaurants created      : {stats['restaurants_created']} (Existing: {stats['restaurants_existing']})")
    print(f"• Menu items inserted      : {stats['menu_items_created']}")
    print(f"• User reviews created     : {stats['reviews_created']}")
    print(f"• Google reviews created   : {stats['google_reviews_created']}")
    print(f"• Favorites created        : {stats['favorites_created']}")
    print("=" * 70)
    print("🔑 DEMO / TEST CREDENTIALS")
    print("=" * 70)
    print("  [ADMIN ACCOUNT]")
    print("  Email    : admin@tastemap.com")
    print("  Username : admin")
    print("  Password : AdminPassword123!")
    print()
    print("  [SAMPLE USER ACCOUNTS]")
    print("  Email    : ahmet.gurme@example.com (Username: gurme_ahmet  | Pass: UserPassword123!)")
    print("  Email    : zeynep.lezzet@example.com (Username: zeynep_lezzet | Pass: UserPassword123!)")
    print("  Email    : can.foodie@example.com (Username: can_foodie    | Pass: UserPassword123!)")
    print("=" * 70)

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Populate TasteMap PostgreSQL database with initial / seed data.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Remove previously seeded test records before re-inserting.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate the seed run without committing to the database.",
    )
    args = parser.parse_args()

    seed_database(reset=args.reset, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
