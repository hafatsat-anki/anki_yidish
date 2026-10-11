



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
{{edit:שאלה 1}}
<div style='font-family: livorna ; font-size: 20px; color: blue;'>{{edit:hint:רמז}}</div>

</td>

    </tr>
  </tbody>
</table> <br> """

card1_back = """
{{FrontSide}}

<hr id=answer>
<div style='font-family: livorna ;  font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
    תשובה
</div>
</tbody>
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
    <tbody>
        <tr>
            <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 1}}</td>
        </tr>
    </tbody>
</table>

<button onclick=showall()>
    ווייזט אלעס
</button>
<button onclick=hideall()>
    באהאלט אלעס
</button>

</tbody>
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
    <tbody>
        <tr>
            <td class="colors" style=" border-radius: 5px; " id=q2>{{edit:שאלה 2}}</td>
        </tr>
    </tbody>
</table>
<button id="bq2" onclick=show("q2")>
    ווייזט שאלה 2
</button>

</tbody>
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
    <tbody>
        <tr>
            <td class="colors" style=" border-radius: 5px; " id=a2>{{edit:תשובה 2}}</td>
        </tr>
    </tbody>
</table>
<button id="ba2" onclick=show("a2")>
    ווייזט תשובה 2
</button>

</tbody>
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
    <tbody>
        <tr>
            <td class="colors" style=" border-radius: 5px; " id=q3>{{edit:שאלה 3}}</td>
        </tr>
    </tbody>
</table>
<button id="bq3" onclick=show("q3")>
    ווייזט שאלה 3
</button>

<div style='font-family: livorna ;  font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
</div>
</tbody>
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
    <tbody>
        <tr>
            <td class="colors" style=" border-radius: 5px; " id=a3>{{edit:תשובה 3}}</td>
        </tr>
    </tbody>
</table>
<button id="ba3" onclick=show("a3")>
    ווייזט תשובה 3
</button>

</tbody>
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
    <tbody>
        <tr>
            <td class="colors" style=" border-radius: 5px; " id=q4>{{edit:שאלה 4}}</td>
        </tr>
    </tbody>
</table>
<button id="bq4" onclick=show("q4")>
    ווייזט שאלה 4
</button>

</tbody>
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
    <tbody>
        <tr>
            <td class="colors" style=" border-radius: 5px; " id=a4>{{edit:תשובה 4}}</td>
        </tr>
    </tbody>
</table>
<button id="ba4" onclick=show("a4")>
    ווייזט תשובה 4
</button>

</tbody>
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
    <tbody>
        <tr>
            <td class="colors" style=" border-radius: 5px; " id=q5>{{edit:שאלה 5}}</td>
        </tr>
    </tbody>
</table>
<button id="bq5" onclick=show("q5")>
    ווייזט שאלה 5
</button>

</tbody>
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
    <tbody>
        <tr>
            <td class="colors" style=" border-radius: 5px; " id=a5>{{edit:תשובה 5}}</td>
        </tr>
    </tbody>
</table>
<button id="ba5" onclick=show("a5")>
    ווייזט תשובה 5
</button>

</tbody>
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
    <tbody>
        <tr>
            <td class="colors" style=" border-radius: 5px; " id=q6>{{edit:שאלה 6}}</td>
        </tr>
    </tbody>
</table>
<button id="bq6" onclick=show("q6")>
    ווייזט שאלה 6
</button>

</tbody>
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
    <tbody>
        <tr>
            <td class="colors" style=" border-radius: 5px; " id=a6>{{edit:תשובה 6}}</td>
        </tr>
    </tbody>
</table>
<button id="ba6" onclick=show("a6")>
    ווייזט תשובה 6
</button>

</tbody>
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
    <tbody>
        <tr>
            <td class="colors" style=" border-radius: 5px; " id=q7>{{edit:שאלה 7}}</td>
        </tr>
    </tbody>
</table>
<button id="bq7" onclick=show("q7")>
    ווייזט שאלה 7
</button>

</tbody>
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
    <tbody>
        <tr>
            <td class="colors" style=" border-radius: 5px; " id=a7>{{edit:תשובה 7}}</td>
        </tr>
    </tbody>
</table>
<button id="ba7" onclick=show("a7")>
    ווייזט תשובה 7
</button>

</tbody>
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
    <tbody>
        <tr>
            <td class="colors" style=" border-radius: 5px; " id=q8>{{edit:שאלה 8}}</td>
        </tr>
    </tbody>
</table>
<button id="bq8" onclick=show("q8")>
    ווייזט שאלה 8
</button>

</tbody>
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
    <tbody>
        <tr>
            <td class="colors" style=" border-radius: 5px; " id=a8>{{edit:תשובה 8}}</td>
        </tr>
    </tbody>
</table>
<button id="ba8" onclick=show("a8")>
    ווייזט תשובה 8
</button>

</tbody>
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
    <tbody>
        <tr>
            <td class="colors" style=" border-radius: 5px; " id=q9>{{edit:שאלה 9}}</td>
        </tr>
    </tbody>
</table>
<button id="bq9" onclick=show("q9")>
    ווייזט שאלה 9
</button>

</tbody>
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
    <tbody>
        <tr>
            <td class="colors" style=" border-radius: 5px; " id=a9>{{edit:תשובה 9}}</td>
        </tr>
    </tbody>
</table>
<button id="ba9" onclick=show("a9")>
    ווייזט תשובה 9
</button>

</tbody>
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
    <tbody>
        <tr>
            <td class="colors" style=" border-radius: 5px; " id=q10>{{edit:שאלה 10}}</td>
        </tr>
    </tbody>
</table>
<button id="bq10" onclick=show("q10")>
    ווייזט שאלה 10
</button>

</tbody>
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
    <tbody>
        <tr>
            <td class="colors" style=" border-radius: 5px; " id=a10>{{edit:תשובה 10}}</td>
        </tr>
    </tbody>
</table>
<button id="ba10" onclick=show("a10")>
    ווייזט תשובה 10
</button>

<script>
    function show(element) {
        var d = document.getElementById(element);
        d.removeAttribute("hidden", "");
        var b = document.getElementById("b" + element);
        b.setAttribute("hidden", "");
        window.pycmd("show!:" + element)
    }
    function showall() {
        const hidden_c_id = ["a2", "a3", "a4", "a5", "a6", "a7", "a8", "a9", "a10", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9", "q10"]
        for (const element of hidden_c_id) {
            try {
                var d = document.getElementById(element);
                d.removeAttribute("hidden", "");
                var b = document.getElementById("b" + element);
                b.setAttribute("hidden", "");
            } catch (error) {
                console.error(error)
            }

            window.pycmd("show!:all")
        }
    }
    function hideall() {
        const hidden_c_id = ["a2", "a3", "a4", "a5", "a6", "a7", "a8", "a9", "a10", "q2", "q3", "q4", "q5", "q6", "q7", "q8", "q9", "q10"]
        for (const element of hidden_c_id) {
            var d = document.getElementById(element);
            try {
                var b = document.getElementById("b" + element);
                if (d.innerText == "") {
                    d.remove();
                    b.remove();
                } else {
                    d.setAttribute("hidden", "");
                    b.removeAttribute("hidden", "");
                }
            } catch (error) {
                console.error(error)
            }

        }
        window.pycmd("hide!:all")
    }
    hideall()
</script>
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
margin-bottom: 2px !important;
}
.nightMode .colors{
 color: white;
 background-color:gray;
}
table {
  border-collapse: revert;
}

button {
    width: 100px;
    font-size: 16px;
    border: none;
    border-radius: 5px;
    -webkit-appearance: none;
    outline: none;
    cursor: pointer;
    margin-right: 10px !important;
 margin-bottom: 10px !important;
    box-shadow: 0 4px 8px 0 rgba(0, 0, 0, 0.2), 0 6px 20px 0 rgba(0, 0, 0, 0.19);
    font-weight: bold;
    color: rgba(70, 70, 70,1);
}
.nightMode .button{
 color: white;
 background-color:gray;
}
"""

few_q_model = "06 עטליכע שאלות און תשובות - נאך דער תשובה קומט נאך א פארבינדענע שאלה (איין קארטל)"
few_q_cards = {"card1":
     {
     "card_name": "עטליכע שאלות און תשובות",
     "card_front": card1_front,
     "card_back": card1_back,
     "card_css": card1_css
    }
}
few_q_fields = {
    "שאלה 1": "שאלה 1",
    "תשובה 1": "תשובה 1",
    "מקור": "מקור",
    "רמז": "רמז",
    "שאלה 2": "שאלה 2",
    "תשובה 2": "תשובה 2",
    "שאלה 3": "שאלה 3",
    "תשובה 3": "תשובה 3",
    "שאלה 4": "שאלה 4",
    "תשובה 4": "תשובה 4",
    "שאלה 5": "שאלה 5",
    "תשובה 5": "תשובה 5",
    "שאלה 6": "שאלה 6",
    "תשובה 6": "תשובה 6",
    "שאלה 7": "שאלה 7",
    "תשובה 7": "תשובה 7",
    "שאלה 8": "שאלה 8",
    "תשובה 8": "תשובה 8",
    "שאלה 9": "שאלה 9",
    "תשובה 9": "תשובה 9",
    "שאלה 10": "שאלה 10",
    "תשובה 10": "תשובה 10"
                   }
few_q_type = {
    "type": 0,
}
