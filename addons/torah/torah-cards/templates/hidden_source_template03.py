



card1_front = """
<div style='font-family: livorna; font-size: 20px; font-weight: bold;text-align:center  '>
שאלה
</div>
<table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
  <tbody >
    <tr>
      <td class = "colors" style="; border-radius: 5px; "><span style=" font-weight: bold;  ">{{edit:hint:מקור}}</span>
{{edit:שאלה}}
<div style='font-family: livorna ; font-size: 20px; color: blue;'>{{edit:hint:רמז}}</div>

</td>

    </tr>
  </tbody>
</table>

"""

card1_back = """
{{FrontSide}}
<hr id=answer>
<div style='font-family: livorna ;  font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
תשובה
</div>
  </tbody>
<table style=" width: 100%;" border="0"
 cellpadding="10" cellspacing="10">
  <tbody>
    <tr>
       <td class = "colors" style="; border-radius: 5px; ">{{edit:תשובה}}</td>
    </tr>
  </tbody>
</table>
"""


card1_css = """
.card {
 font-family: livorna;
 font-size: 18pt;
 text-align: center;
  background-color:lightgray;
text-align: justify;
direction: rtl;
unicode-bidi: embed;
}
.colors{
 color: black;
 background-color:lightyellow;
}
.nightMode .colors{
 color: white;
 background-color:gray;
}
"""

hidden_source_model = "03 געווענליכע שאלה מיט א באהאלטענעם מקור אלס רמז (איין קארטל)"
hidden_source_cards = {"card1":
     {
     "card_name": "תורני - באהאלטענער מקור (אויך פאר א בחינה אויף די מקורות)",
     "card_front": card1_front,
     "card_back": card1_back,
     "card_css": card1_css
    }
}
hidden_source_fields = {
    "שאלה": "שאלה",
    "תשובה": "תשובה",
    "מקור": "מקור",
    "רמז": "רמז"
}
o2tmm_type = {
    "type": 0,
}

