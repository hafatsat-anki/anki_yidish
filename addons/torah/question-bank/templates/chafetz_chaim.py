



card1_front = """
<div style='font-family: livorna; font-size: 20px; font-weight: bold;text-align:center  '>
שאלה
</div>
<table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
  <tbody >
    <tr>
      <td class = "colors" style="; border-radius: 5px; ">
      <span style=" font-weight: bold;  ">{{edit:מקור}}</span>
{{#מקור}}

 {{/מקור}}
{{edit:שאלה}}
<div style='font-family: livorna ; font-size: 20px; color: blue;'>{{edit:hint:רמז}}</div>

</td>

    </tr>
  </tbody>
</table>

<div id="zl1" style="text-align: center;"><span style="font-size: 10pt;"><strong><span style="font-family: 'arial black', sans-serif;">לעילוי נשמת ר' יעקב בן מרדכי וזוהרה ז"ל</span></strong></span></div>
<div id="zl2" style="text-align: center;"><span style="font-size: 10pt;"><strong><span style="font-family: 'arial black', sans-serif;">ואולגה בת חיים ואסתר ע"ה.</span></strong></span></div>
<div id="ts" style="text-align: center;"><span style="font-size: 10pt;"><strong><span style="font-family: 'arial black', sans-serif;">פאר יעדן ענין וועגן די שאלות קענט איר זיך ווענדן צו הפצת אנקי - <a href="mailto:anki4tora@gmail.com">anki4tora@gmail.com</a></span></strong></span></div>
  """

card1_back = """

<div style='font-family: livorna; font-size: 20px; font-weight: bold;text-align:center  '>
שאלה
</div>
<table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
  <tbody >
    <tr>
      <td class = "colors" style="; border-radius: 5px; ">
      <span style=" font-weight: bold;  ">{{edit:מקור}}</span>
{{#מקור}}

 {{/מקור}}
{{edit:שאלה}}
<div style='font-family: livorna ; font-size: 20px; color: blue;'>{{edit:hint:רמז}}</div>

</td>

    </tr>
  </tbody>
</table>

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

<div id="zl1" style="text-align: center;"><span style="font-size: 10pt;"><strong><span style="font-family: 'arial black', sans-serif;">לעילוי נשמת ר' יעקב בן מרדכי וזוהרה ז"ל</span></strong></span></div>
<div id="zl2" style="text-align: center;"><span style="font-size: 10pt;"><strong><span style="font-family: 'arial black', sans-serif;">ואולגה בת חיים ואסתר ע"ה.</span></strong></span></div>
<div id="ts" style="text-align: center;"><span style="font-size: 10pt;"><strong><span style="font-family: 'arial black', sans-serif;">פאר יעדן ענין וועגן די שאלות קענט איר זיך ווענדן צו הפצת אנקי - <a href="mailto:anki4tora@gmail.com">anki4tora@gmail.com</a></span></strong></span></div>
 """


card1_css = """
.card {
 font-family: livorna;
 font-size: 24px;
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

cc_model = "תת_לשימוש_המאגר_המוכן_חפץ_חיים"
cc_cards = {"card1":
     {
     "card_name": 'חפץ_חיים',
     "card_front": card1_front,
     "card_back": card1_back,
     "card_css": card1_css
    }
}
cc_fields = {
    "שאלה": "שאלה",
    "תשובה": "תשובה",
    "מקור": "מקור",
    "רמז": "רמז"
}
cc_type = {
    "type": 0,
}
