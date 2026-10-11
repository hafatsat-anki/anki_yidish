



card1_front = """
<div style='font-family: livorna; font-size: 20px; font-weight: bold;text-align:center  '>
שאלה
</div>
<table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
  <tbody >
    <tr>
      <td class = "colors" style="; border-radius: 5px; "><span style=" font-weight: bold;  ">{{edit:מקור}}</span>
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

standard_model = "01 געווענליכע שאלה (איין קארטל)"
standard_cards = {"card1":
     {
     "card_name": "געווענליכע שאלה",
     "card_front": card1_front,
     "card_back": card1_back,
     "card_css": card1_css
    }
}
standard_fields = {
    "שאלה": "שאלה",
    "תשובה": "תשובה",
    "מקור": "מקור",
    "רמז": "רמז"
}
standard_type = {
    "type": 0,
}

