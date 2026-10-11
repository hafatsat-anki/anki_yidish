



card1_front = """

<table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
  <tbody >
    <tr>
      <td class = "colors" style="; border-radius: 5px; ">
      <span style=" font-weight: bold;  ">{{edit:מקור}}</span>
{{edit:cloze:טקסט}}

<div style='font-family: livorna ; font-size: 20px; color: blue;'>{{edit:hint:רמז}}</div>

</td>

    </tr>
  </tbody>
</table>
"""

card1_back = """
<table style=" width: 100%;" border="0"
 cellpadding="10" cellspacing="10">
  <tbody>
    <tr>
     <td class = "colors" style="; border-radius: 5px; ">
       <span style=" font-weight: bold;">{{edit:מקור}}</span>
        {{edit:cloze:טקסט}}
        <div style='font-family: livorna ; font-size: 20px; color: blue;'>{{edit:hint:רמז}}</div>
        {{edit:הוספות}}</td>
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
.cloze {
 font-weight: bold;
 color: blue;
}
.nightMode .cloze {
 color: lightblue;
}

"""

cloze_model = "08 פילט אויס דאס אויסגעלאזטע - א טייל אינהאלט איז באהאלטן (דער צאל קארטלעך ווענדט זיך אין די באהאלטונגען; איין אדער מער אין א שאלה אדער באזונדערע קארטלעך)"
cloze_cards = {"card1":
     {
     "card_name": "פילט אויס דאס אויסגעלאזטע",
     "card_front": card1_front,
     "card_back": card1_back,
     "card_css": card1_css
    }
}
cloze_fields = {
    "טקסט": "טקסט",
    "הוספות": "הוספות",
    "מקור": "מקור",
    "רמז": "רמז"
}
cloze_type = {
    "type": 1,
}

