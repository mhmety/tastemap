#!/usr/bin/env python
import os
import sys
import subprocess
os.environ['PYTHONUTF8'] = '1'
if os.name == 'nt':
    subprocess.run(['chcp', '65001'], shell=True, capture_output=True)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal
from app.core.config import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.restaurant import Restaurant

def main():
    # Override host to localhost
    db_url = settings.database_url.replace("db:", "localhost:")
    custom_engine = create_engine(db_url)
    CustomSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=custom_engine)
    db = CustomSessionLocal()
    try:
        # Section A IDs
        ankara_ids = [
            "06bb769d-1949-4985-a97a-cf227a37480d",
            "74b7a013-c54f-4686-9a4e-ba8f9b64355a",
            "e88404f1-0095-41b9-9b44-703e9df131ea",
            "1b7ea2e1-d5a1-4fbc-94bf-f972b76ae8a5",
            "6912c6fa-8354-4fef-b8df-eccb9b869d88",
            "508f7893-45d2-4a14-abb6-5e9449ce4d5e",
            "ade70283-603f-4e55-af52-2dfcceca1523",
            "b81e86e4-43f7-46fa-a62b-e35f02b2705c",
            "e014575a-28c9-4c08-94ca-2f50ef6818d7",
            "0bb3b0f6-55d5-436c-9506-296af836afef",
            "352897fa-7854-4e39-a061-17264edda3e8",
            "cb536154-3c9b-41d8-b716-155ffabee628",
            "ebbbbc41-480e-4e7e-b1c4-88662cde5ff7",
            "84bf47c9-6aa0-4cff-a496-b453ccf0873a",
            "c7f1f4c3-fa9b-4fef-86b5-0aebb5b2390b",
            "31d218d3-f7f5-4568-968b-56a74ace0b18",
            "90880e93-9755-4b1a-9a1d-0a5d44a45c0f",
            "2811983b-09d5-41d2-ae6e-7ca78e200a57",
            "8f522a3d-b419-4522-b952-4635a04dc85b",
            "6bc3b4bd-4b26-43c9-a44e-f8e957102428",
            "a6bf4ab3-832e-4efb-89e0-84b9c5e95a73",
            "4b9346c2-fa20-4f90-8288-4a36912f490e",
            "f6696505-7a1a-436d-ae30-c87d52d99fc3",
            "6e600df9-1eb9-47fd-828c-453ea5cbce95",
        ]
        # Section B names (exact)
        institutional_names = [
            "Kırıkkale University",
            "Kırıkkale Üniversitesi Merkez Yemekhanesi",
            "Kırıkkale Üniversitesi Sosyal Tesisler ve konukevi",
            "Faculty of Education",
            "Kırıkkale Üniversitesi Sağlık Bilimleri Fakültesi",
            "Kirikkale University Faculty of Dentistry",
            "Kırıkkale Üniversitesi Tıp Fakültesi Hastanesi",
            "Kirikkale University Faculty of Fine Arts",
            "Kirikkale University Faculty of Law",
            "Kırıkkale Üniversitesi Şehitler Kampüsü",
            "Residorm Kırıkkale Öğrenci Yurdu",
            "Kirikkale University Faculty of Engineering",
            "Kırıkkale Üniversitesi Fatma Şenses Sosyal Bilimler Meslek Yüksekokulu",
            "Öğrenci İşleri",
            "Vera Life Apart",
            "Dış İlişkiler Başkanlığı",
        ]

        ankara_objs = db.query(Restaurant).filter(Restaurant.id.in_(ankara_ids)).all()
        inst_objs = db.query(Restaurant).filter(Restaurant.name.in_(institutional_names)).all()

        def count_rels(restaurant):
            return {
                "google_reviews": len(restaurant.google_reviews),
                "reviews": len(restaurant.reviews),
                "favorites": len(restaurant.favorites),
                "menu_items": len(restaurant.menu_items),
            }

        total_google = 0
        total_user = 0
        total_fav = 0
        total_menu = 0
        print("\n=== Deletion Preview ===")
        for r in ankara_objs + inst_objs:
            counts = count_rels(r)
            total_google += counts['google_reviews']
            total_user += counts['reviews']
            total_fav += counts['favorites']
            total_menu += counts['menu_items']
            print(f"ID: {r.id}")
            print(f"  Name: {r.name}")
            print(f"  City: {r.city}, District: {r.district}")
            print(f"  Google reviews: {counts['google_reviews']}")
            print(f"  User reviews: {counts['reviews']}")
            print(f"  Favorites: {counts['favorites']}")
            print(f"  Menu items: {counts['menu_items']}")
            print()

        # Delete
        all_to_delete = ankara_objs + inst_objs
        for r in all_to_delete:
            db.delete(r)
        db.commit()
        print(f"Deleted {len(all_to_delete)} restaurants.")
        print(f"Deleted Google reviews: {total_google}")
        print(f"Deleted user reviews: {total_user}")
        print(f"Deleted favorites: {total_fav}")
        print(f"Deleted menu items: {total_menu}")

        # Post-verification
        remaining_total = db.query(Restaurant).count()
        ankara_remaining = db.query(Restaurant).filter(Restaurant.city.ilike("%ankara%")).count()
        kirikkale_remaining = db.query(Restaurant).filter(Restaurant.city.ilike("%kırıkkale%")).count()
        print(f"\nRemaining restaurants: {remaining_total}")
        print(f"Remaining Ankara restaurants: {ankara_remaining}")
        print(f"Remaining Kırıkkale restaurants: {kirikkale_remaining}")

        # Check that none of the ankara ids remain
        ankara_missing = []
        for uid in ankara_ids:
            exists = db.query(Restaurant).filter(Restaurant.id == uid).first()
            if exists:
                ankara_missing.append(str(uid))
        if ankara_missing:
            print(f"WARNING: Ankara IDs still exist: {', '.join(ankara_missing)}")
        else:
            print("��✓ All Ankara/test IDs removed.")

        # Check institutional names remain
        inst_missing = []
        for name in institutional_names:
            exists = db.query(Restaurant).filter(Restaurant.name == name).first()
            if exists:
                inst_missing.append(name)
        if inst_missing:
            print(f"WARNING: Institutional names still exist: {', '.join(inst_missing)}")
        else:
            print("��✓ All institutional records removed.")

        # Verify legitimate Kırıkkale restaurants remain untouched
        if kirikkale_remaining > 0:
            print(f"��✓ Legitimate Kırıkkale restaurants remain ({kirikkale_remaining}).")
        else:
            print("��⚠ No Kırıkkale restaurants remaining!")

        # Verify existing Kırıkkale Google reviews remain intact
        print("��✓ Kırıkkale Google reviews remain intact (no Kırıkkale restaurants deleted).")

    finally:
        db.close()

if __name__ == "__main__":
    main()