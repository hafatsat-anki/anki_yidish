



card1_front = """
<div style='font-family: livorna; font-size: 20px; font-weight: bold;text-align:center  '>
שאלה
</div>
<table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
  <tbody >
    <tr>
      <td class = "colors" style="; border-radius: 5px; ">
      <span style=" font-weight: bold;  ">{{edit:מסכת ודף}}</span>
{{edit:שאלה}}
<div style='font-family: livorna ; font-size: 20px; color: blue;'>{{edit:hint:רמז}}</div>

</td>

    </tr>
  </tbody>
</table> """

card1_back = """
{{FrontSide}}

<div style='font-family: livorna; font-size: 20px; font-weight: bold;text-align:center  '>
תשובה
</div>
<table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
  <tbody >
    <tr>
      <td class = "colors" style="; border-radius: 5px; ">
     {{edit:תשובה}}
</td>
    </tr>
  </tbody>
</table>

<table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
  <tbody >
    <tr>
      <td class = "colors" style="; border-radius: 5px; ">
<div style='font-family: Arial; font-size: 20px;'>{{edit:hint:תשובה מלאה}}</div>

</td>
    </tr>
  </tbody>
</table>
<table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
  <tbody >
    <tr>
      <td class = "colors" style="; border-radius: 5px; ">
<div style='font-family: Arial; font-size: 20px;'>{{edit:hint:צילום הדף}}</div>
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

standard_with_extended_model = "02 שאלות מיט א בילד פונעם בלאט און אן אויספירליכע תשובה (איין קארטל)"
standard_with_extended_cards = {"card1":
     {
     "card_name": "שאלות מיט א בילד פונעם בלאט און אן אויספירליכע תשובה",
     "card_front": card1_front,
     "card_back": card1_back,
     "card_css": card1_css
    }
}
standard_with_extended_fields = {
    "שאלה": "שאלה",
    "תשובה": "תשובה",
    "מסכת ודף": "מסכת ודף",
    "רמז": "רמז",
    "תשובה מלאה": "תשובה מלאה",
    "צילום הדף": "צילום הדף"
}
standard_with_extended_type = {
    "type": 0,
}

