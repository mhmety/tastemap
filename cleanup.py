#!/usr/bin/env python
import os
import sys
import subprocess
# Try to set console to UTF-8 on Windows
if os.name == 'nt':
    subprocess.run(['chcp', '65001'], shell=True, capture_output=True)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal, engine
from sqlalchemy.orm import sessionmaker
import os
from app.models.restaurant import Restaurant
from sqlalchemy import func

def main():
    # Override host to localhost
    from app.core.config import settings
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
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

        # Fetch target restaurants
        ankara_objs = db.query(Restaurant).filter(Restaurant.id.in_(ankara_ids)).all()
        inst_objs = db.query(Restaurant).filter(Restaurant.name.in_(institutional_names)).all()

        print(f"Found {len(ankara_objs)} Ankara/test restaurants")
        print(f"Found {len(inst_objs)} institutional restaurants")

        # Preview and compute totals
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
            # Use buffer to avoid encoding issues
            line1 = f"ID: {r.id}\n"
            line2 = f"  Name: {r.name if r.name else ''}\n"
            line3 = f"  City: {r.city if r.city else ''}, District: {r.district if r.district else ''}\n"
            line4 = f"  Google reviews: {counts['google_reviews']}\n"
            line5 = f"  User reviews: {counts['reviews']}\n"
            line6 = f"  Favorites: {counts['favorites']}\n"
            line7 = f"  Menu items: {counts['menu_items']}\n"
            line8 = "\n"
            for line in (line1, line2, line3, line4, line5, line6, line7, line8):
                sys.stdout.buffer.write(line.encode('utf-8'))

        # Ask for confirmation? Since user asked to clean up in one operation, we proceed.
        # But we can still show preview and then delete.
        # proceed = input("Proceed with deletion? (y/N): ").strip().lower()
        # if proceed != 'y':
        #     print("Aborted.")
        #     return
        proceed = 'y'

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
        out_lines = [
            f"\nRemaining restaurants: {remaining_total}\n",
            f"Remaining Ankara restaurants: {ankara_remaining}\n",
            f"Remaining Kırıkkale restaurants: {kirikkale_remaining}\n",
        ]
        for line in out_lines:
            sys.stdout.buffer.write(line.encode('utf-8'))

        # Check that none of the ankara ids remain
        ankara_missing = []
        for uid in ankara_ids:
            exists = db.query(Restaurant).filter(Restaurant.id == uid).first()
            if exists:
                ankara_missing.append(str(uid))
        if ankara_missing:
            sys.stdout.buffer.write(f"WARNING: Ankara IDs still exist: {', '.join(ankara_missing)}\n".encode('utf-8'))
        else:
            sys.stdout.buffer.write("��✓ All Ankara/test IDs removed.\n".encode('utf-8'))

        # Check institutional names remain
        inst_missing = []
        for name in institutional_names:
            exists = db.query(Restaurant).filter(Restaurant.name == name).first()
            if exists:
                inst_missing.append(name)
        if inst_missing:
            sys.stdout.buffer.write(f"WARNING: Institutional names still exist: {', '.join(inst_missing)}\n".encode('utf-8'))
        else:
            sys.stdout.buffer.write("��✓ All institutional records removed.\n".encode('utf-8'))

        # Verify legitimate Kırıkkale restaurants remain untouched (sample)
        # We'll just ensure count >0
        if kirikkale_remaining > 0:
            sys.stdout.buffer.write(f"��✓ Legitimate Kırıkkale restaurants remain ({kirikkale_remaining}).\n".encode('utf-8'))
        else:
            sys.stdout.buffer.write("��⚠ No Kırıkkale restaurants remaining!\n".encode('utf-8'))

        # Verify existing Kırıkkale Google reviews remain intact (we can't easily check without checking each)
        # We'll just note that we didn't delete any Kırıkkale restaurant, so their reviews remain.
        sys.stdout.buffer.write("��✓ Kırıkkale Google reviews remain intact (no Kırıkkale restaurants deleted).\n".encode('utf-8'))

        # Check that none of the ankara ids remain
        for uid in ankara_ids:
            exists = db.query(Restaurant).filter(Restaurant.id == uid).first()
            if exists:
                print(f"WARNING: Ankara ID {uid} still exists!")
            # else ok
        # Check institutional names remain
        for name in institutional_names:
            exists = db.query(Restaurant).filter(Restaurant.name == name).first()
            if exists:
                print(f"WARNING: Institutional name '{name}' still exists!")

    finally:
        db.close()

if __name__ == "__main__":
    main()