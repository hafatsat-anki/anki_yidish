



card1_front = """
<table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
  <tbody >
    <tr>
      <td class = "colors" style="; border-radius: 5px; ">
{{edit:שאלה}}
{{edit:מקור}}
{{edit:type:תשובה}}
{{edit:רמז}}

</td>

    </tr>
  </tbody>
</table>
"""

card1_back = """
<table style= " width: 100%; "
 cellpadding="10" cellspacing="10">
  <tbody >
    <tr>
      <td class = "colors" style="; border-radius: 5px; ">

{{edit:שאלה}}
{{edit:מקור}}
{{edit:type:תשובה}}
{{edit:רמז}}
</td>

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

type_ans_model = "04 שרייבט אריין די תשובה (איין קארטל)"
type_ans_cards = {"card1":
     {
     "card_name": "שרייבט אריין די תשובה",
     "card_front": card1_front,
     "card_back": card1_back,
     "card_css": card1_css
    }
}
type_ans_fields = {
    "שאלה": "שאלה",
    "תשובה": "תשובה",
    "מקור": "מקור",
    "רמז": "רמז"
}
type_ans_type = {
    "type": 0,
}

