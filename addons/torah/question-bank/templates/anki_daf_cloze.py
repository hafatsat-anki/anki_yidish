



card1_front = """
{{cloze:Text}}
 """

card1_back = """
{{cloze:Text}}<br>
<div style='font-family: Arial; font-size: 14px;'>{{מקור}}</div>
<div style='font-family: Arial; font-size: 6px;'><br></div>
<div style='font-family: Arial; font-size: 10px;'>©<br> <a href="http://www.ankitorah.com/anki-daf">www.ankitorah.com/anki-daf</a>
<br><a href="http://www.masterdafaweek.com">www.masterdafaweek.com</a>
<div style='font-family: Arial; font-size: 10px;'>{{Sponsorship}}</div> """


card1_css = """
.card {
 font-family: arial;
 font-size: 20px;
 text-align: center;
 color: black;
 background-color: white;
}

.cloze {
 font-weight: bold;
 color: blue;
}
"""

adc_model = "Anki-Daf-cloze"
adc_cards = {"card1":
     {
     "card_name": "Card 1",
     "card_front": card1_front,
     "card_back": card1_back,
     "card_css": card1_css
    }
}
adc_fields = {
    "Text": "Text",
    "מקור": "מקור",
    "Sponsorship": "Sponsorship"
}
adc_type = {
    "type": 0,
}
