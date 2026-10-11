



card1_front = """
<div style='font-family: livorna; font-size: 20px; font-weight: bold;text-align:center  '>
שאלה
</div>
<table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
  <tbody >
    <tr>
      <td class = "colors" style="; border-radius: 5px; ">
מה הם הנושאים ב: {{{edit:מיקום (מסכת ודף / פרשה ופרק וכדו')}}
<div style='font-family: livorna ; font-size: 20px; color: blue;'>{{edit:hint:רמז}}</div>

</td>

    </tr>
  </tbody>
</table> """

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
     <td class = "colors" style="; border-radius: 5px; ">{{edit:הנושאים}}</td>
    </tr>
  </tbody>
</table>
"""

card2_front = """
<div style='font-family: livorna; font-size: 20px; font-weight: bold;text-align:center  '>
שאלה
</div>
<table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
  <tbody >
    <tr>
      <td class = "colors" style="; border-radius: 5px; ">
וואו זענען די פאלגנדע נושאים: <br> {{{edit:הנושאים}}
<div style='font-family: livorna ; font-size: 20px; color: blue;'>{{edit:hint:רמז}}</div>

</td>

    </tr>
  </tbody>
</table> """

card2_back = """
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
     <td class = "colors" style="; border-radius: 5px; ">{{edit:מיקום (מסכת ודף / פרשה ופרק וכדו')}}</td>
    </tr>
  </tbody>
</table>
"""

card_css  = """
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

subject_and_source_model = "05 בחינה אויף נושאים און מקורות (צוויי קארטלעך: וואו שטייט עס און וואס שטייט אין א מקור)"
subject_and_source_cards = {"card1":
     {
     "card_name": "קארטל 1 - בחינה אויף די נושאים",
     "card_front": card1_front,
     "card_back": card1_back,
     "card_css": card_css
    },"card2":
     {
     "card_name": "קארטל 2 - בחינה אויפן פלאץ",
     "card_front": card2_front,
     "card_back": card2_back,
     "card_css": card_css
    }
}
subject_and_source_fields = {
    "נושאים": "הנושאים",
    "loc": "מיקום (מסכת ודף / פרשה ופרק וכדו')",
    "רמז": "רמז"
}
subject_and_source_type = {
    "type": 0,
}
