from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Category, Base, Items, User
from datetime import datetime

engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

User1 = User(name="Admin", email="aaa@aaa.com")
session.add(User1)
session.commit()

category1 = Category(user_id=1,name="Phones")
session.add(category1)
session.commit()

description = '''The Samsung Galaxy S6 edge is a smartphone that runs on
 the Android operating system. It has a 5.1-inch touch-screen display,
 measures 5.6 by 2.8 by 0.3 inches and weighs 4.6 ounces.'''
item1 = Items(user_id=1,name="Galaxy S6 edge",description=description,
              time=str(datetime.now()),category=category1)
session.add(item1)
session.commit()

description = '''iPhone X (Roman numeral "X" pronounced "ten",
although colloquially, sometimes pronounced as the name of the letter)
is a smartphone designed, developed, and marketed by Apple Inc.
 It was the eleventh generation of the iPhone.'''

item1 = Items(user_id=1,name="iPhone X",description=description,
              time=str(datetime.now()),category=category1)
session.add(item1)
session.commit()

category2 = Category(user_id=1,name="Cameras")
session.add(category2)
session.commit()

description = '''EOS 6D is the world's lightest* full-frame DSLR equipped with a
20.2 megapixel CMOS sensor with precision 11-point AF system and also offers
 built-in WiFi and GPS support**.

* Lightest full-frame DSLR as of 13 September 2012, a Canon survey.

** There is also a 6D variant model without built-in WiFi and GPS.'''

item2 = Items(user_id=1,name="Canon EOS 6D",description=description,
              time=str(datetime.now()),category=category2)
session.add(item2)
session.commit()


category3 = Category(user_id=1,name="Projectors")
session.add(category3)
session.commit()

category4 = Category(user_id=1,name="Printers")
session.add(category4)
session.commit()

category5 = Category(user_id=1,name="LapTops")
session.add(category5)
session.commit()

description = '''Intel Core i7-4700HQ 2.4GHz (Turbo 3.4 GHz).
1TB Hard Drive. 8GB RAM. NVIDIA GTX850M 2GB-VRAM.
15.6-Inch Full-HD IPS Touchscreen Display. 720P HD Webcam.
3x USB 3.0, 1x HDMI, 1x MiniDisplay. SDXC Card Reader. 802.11 A/C, Gigabit ethernet port.
Aluminum body construction. Includes external plug-in mini-Subwoofer.'''

item3 = Items(user_id=1,name="ASUS N550J",description=description,
              time=str(datetime.now()),category=category5)
session.add(item3)
session.commit()

category6 = Category(user_id=1,name="Smart Board")
session.add(category6)
session.commit()

print("New Category and Items Added.")
