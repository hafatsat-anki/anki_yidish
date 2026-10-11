



card1_front = """
{{Front}}
<br>
{{hint:hint}}
 """

card1_back = """
{{Front}}

<hr id=answer>

{{Back}}

<div style='font-family: Arial; font-size: 14px;'>{{מקור}}</div>
<div style='font-family: Arial; font-size: 6px;'><br></div>
<div style='font-family: Arial; font-size: 10px;'>©<br> <a href="http://www.ankidaf.com">www.ankidaf.com</a>
<br><a href="http://www.masterdafaweek.com">www.masterdafaweek.com</a>
<div style='font-family: Arial; font-size: 10px;'>{{Sponsorship}}</div>
"""


card1_css = """
.card {
 font-family: arial;
 font-size: 20px;
 text-align: center;
 color: black;
 background-color: white;
}
"""

ad_model = "AnkiDaf"
ad_cards = {"card1":
     {
     "card_name": "Card 1",
     "card_front": card1_front,
     "card_back": card1_back,
     "card_css": card1_css
    }
}
ad_fields = {
    "Front": "Front",
    "Back": "Back",
    "מקור": "מקור",
    "hint": "hint",
    "Sponsorship": "Sponsorship"
}
ad_type = {
    "type": 0,
}
