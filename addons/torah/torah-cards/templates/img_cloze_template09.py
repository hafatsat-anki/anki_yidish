



card1_front = """
<table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
  <tbody >
    <tr>
      <td class = "colors" style="; border-radius: 5px; ">
      <span style=" font-weight: bold;  ">
{{#כותרת}}<div>{{edit:כותרת}}</div>{{/כותרת}}</span>
<div>{{edit:מקור}}</div>
<div style='font-family: livorna ; font-size: 20px; color: blue;'>{{edit:hint:רמז}}</div>
<div style="display: none">{{edit:cloze:הסתרה}}
</div>
<div id="err"></div>
<div id="image-occlusion-container">
    {{edit:תמונה}}
    <canvas id="image-occlusion-canvas"></canvas>
</div>


</td>

    </tr>
  </tbody>
</table>
<script>
try {
    anki.imageOcclusion.setup();
} catch (exc) {
    document.getElementById("err").innerHTML = `שגיאה בטעינת הסתרת תמונה. האם גרסת ה-Anki שלך מעודכנת?<br><br>${exc}`;
}
</script>

<div style='font-family: "Arial"; font-size: 20px;'>{{edit:הערות}}</div>
"""

card1_back = """
<table style=" width: 100%;" border="0"
 cellpadding="10" cellspacing="10">
  <tbody>
    <tr>
     <td class = "colors" style="; border-radius: 5px; ">
       <span style=" font-weight: bold;">
{{#כותרת}}<div>{{edit:כותרת}}</div>{{/כותרת}}
</span>
  <div>{{edit:מקור}}</div>
  <div style='font-family: livorna ; font-size: 20px; color: blue;'>{{edit:hint:רמז}}</div>
<div style="display: none">{{edit:cloze:הסתרה}}</div>
<div id="err"></div>
<div id="image-occlusion-container">
    {{edit:תמונה}}
    <canvas id="image-occlusion-canvas"></canvas>
</div>

<div><button id="toggle">טוישט די באהאלטונגען</button></div>
{{#תוספת לתשובה}}<div>{{edit:תוספת לתשובה}}</div>{{/תוספת לתשובה}}
</td>
    </tr>
  </tbody>
</table>
<script>
try {
    anki.imageOcclusion.setup();
} catch (exc) {
    document.getElementById("err").innerHTML = `שגיאה בטעינת הסתרת תמונה. האם גרסת ה-Anki שלך מעודכנת?<br><br>${exc}`;
}
</script>
"""


card1_css = """
#image-occlusion-canvas {
    --inactive-shape-color: #ffeba2;
    --active-shape-color: #ff8e8e;
    --inactive-shape-border: 1px #212121;
    --active-shape-border: 1px #212121;
}
#image-occlusion-container{
  left: initial !important;
  transform: initial !important;
  margin-left: auto;
  margin-right: auto;
}
.card {
 font-family: livorna;
 font-size: 18pt;
 text-align: center;
  background-color:lightgray;
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

left: unset !important;
right: 0 ;
"""

img_cloze_model = "09 פילט אויס דאס אויסגעלאזטע - בילד"
img_cloze_cards = {"card1":
     {
     "card_name": "פילט אויס דאס אויסגעלאזטע - בילד",
     "card_front": card1_front,
     "card_back": card1_back,
     "card_css": card1_css
    }
}
img_cloze_fields = {
    "הסתרה": "הסתרה",
    "תמונה": "תמונה",
    "כותרת": "כותרת",
    "מקור": "מקור",
    "רמז": "רמז",
    "תוספת לתשובה": "תוספת לתשובה",
    "הערות": "הערות"
}
img_cloze_type = {
    "type": 1,
}

