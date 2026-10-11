

card1_front = """
<div style='font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
שאלה
</div>
<table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
 <tbody >
 <tr>
 <td class = "colors" style="; border-radius: 5px; ">
 <span style=" font-weight: bold; ">{{#מקור}}{{edit:מקור}}{{/מקור}}</span>
{{#שאלה 1}}{{edit:שאלה 1}}{{/שאלה 1}}
<div style='font-family: livorna ; font-size: 20px; color: blue;'>{{#רמז}}{{edit:hint:רמז}}{{/רמז}}</div>

</td>

 </tr>
 </tbody>

</table>
 <br> """

card1_back = """
{{FrontSide}}

<hr id=answer>
<div style='font-family: livorna ; font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
 תשובה
</div>
</tbody>

{{#תשובה 1}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 1}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 1}}

<button onclick=showall()>
 ווייזט אלעס
</button>
<button onclick=hideall()>
 באהאלט אלעס
</button>
{{#שאלה 2}}
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
{{/שאלה 2}}
{{#תשובה 2}}
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
{{/תשובה 2}}
</tbody>
{{#שאלה 3}}

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
{{/שאלה 3}}

</tbody>

{{#תשובה 3}}
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
{{/תשובה 3}}

</tbody>

{{#שאלה 4}}
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
{{/שאלה 4}}

</tbody>
{{#תשובה 4}}
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
{{/תשובה 4}}

</tbody>
{{#שאלה 5}}
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
{{/שאלה 5}}

</tbody>
{{#תשובה 5}}
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
{{/תשובה 5}}

</tbody>
{{#שאלה 6}}
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
{{/שאלה 6}}

</tbody>
{{#תשובה 6}}
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
{{/תשובה 6}}

</tbody>
{{#שאלה 7}}
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
{{/שאלה 7}}
</tbody>
{{#תשובה 7}}
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
{{/תשובה 7}}
</tbody>
{{#שאלה 8}}
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
{{/שאלה 8}}
</tbody>
{{#תשובה 8}}
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
{{/תשובה 8}}
</tbody>
{{#שאלה 9}}
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
{{/שאלה 9}}
</tbody>
{{#תשובה 9}}
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
{{/תשובה 9}}
</tbody>
{{#שאלה 10}}
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
{{/שאלה 10}}
</tbody>
{{#תשובה 10}}
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
{{/תשובה 10}}
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
 console.log(error)
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
 console.log(error)
 }

 }
 window.pycmd("hide!:all")
 }
 hideall()
</script>
"""
card2_front = """
{{#שאלה 2}}
 <div style='font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
 שאלה
 </div>
 <table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
 <tbody >
 <tr>
 <td class = "colors" style="; border-radius: 5px; ">
 <span style=" font-weight: bold; ">{{#מקור}}{{edit:מקור}}{{/מקור}}</span>
 {{#שאלה 1}}{{edit:שאלה 1}}{{/שאלה 1}}
 <div style='font-family: livorna ; font-size: 20px; color: blue;'>{{#רמז}}{{edit:hint:רמז}}{{/רמז}}</div>

 </td>

 </tr>
 </tbody>

 </table>
 <br>

</tbody>
{{#תשובה 1}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 1}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 1}}
{{#שאלה 2}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 2}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 2}}

</tbody>
{{/שאלה 2}}
"""

card2_back = """
{{FrontSide}}

<hr id=answer>
<div style='font-family: livorna ; font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
 תשובה
</div>
</tbody>

{{#תשובה 2}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 2}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 2}}

<button onclick=showall()>
 ווייזט אלעס
</button>
<button onclick=hideall()>
 באהאלט אלעס
</button>
</tbody>
{{#שאלה 3}}

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
{{/שאלה 3}}

</tbody>

{{#תשובה 3}}
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
{{/תשובה 3}}

</tbody>

{{#שאלה 4}}
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
{{/שאלה 4}}

</tbody>
{{#תשובה 4}}
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
{{/תשובה 4}}

</tbody>
{{#שאלה 5}}
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
{{/שאלה 5}}

</tbody>
{{#תשובה 5}}
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
{{/תשובה 5}}

</tbody>
{{#שאלה 6}}
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
{{/שאלה 6}}

</tbody>
{{#תשובה 6}}
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
{{/תשובה 6}}

</tbody>
{{#שאלה 7}}
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
{{/שאלה 7}}
</tbody>
{{#תשובה 7}}
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
{{/תשובה 7}}
</tbody>
{{#שאלה 8}}
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
{{/שאלה 8}}
</tbody>
{{#תשובה 8}}
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
{{/תשובה 8}}
</tbody>
{{#שאלה 9}}
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
{{/שאלה 9}}
</tbody>
{{#תשובה 9}}
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
{{/תשובה 9}}
</tbody>
{{#שאלה 10}}
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
{{/שאלה 10}}
</tbody>
{{#תשובה 10}}
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
{{/תשובה 10}}
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
 console.log(error)
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
 console.log(error)
 }

 }
 window.pycmd("hide!:all")
 }
 hideall()
</script>
"""
card3_front = """
{{#שאלה 3}}
 <div style='font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
 שאלה
 </div>
 <table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
 <tbody >
 <tr>
 <td class = "colors" style="; border-radius: 5px; ">
 <span style=" font-weight: bold; ">{{#מקור}}{{edit:מקור}}{{/מקור}}</span>
 {{#שאלה 1}}{{edit:שאלה 1}}{{/שאלה 1}}
 <div style='font-family: livorna ; font-size: 20px; color: blue;'>{{#רמז}}{{edit:hint:רמז}}{{/רמז}}</div>

 </td>

 </tr>
 </tbody>

 </table>
 <br>

</tbody>
{{#תשובה 1}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 1}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 1}}
{{#שאלה 2}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 2}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 2}}

</tbody>
{{#תשובה 2}}

<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 2}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 2}}
{{#שאלה 3}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 3}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 3}}

</tbody>

{{/שאלה 3}}
"""

card3_back = """
{{FrontSide}}

<hr id=answer>
<div style='font-family: livorna ; font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
 תשובה
</div>
</tbody>

{{#תשובה 3}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 3}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 3}}

<button onclick=showall()>
 ווייזט אלעס
</button>
<button onclick=hideall()>
 באהאלט אלעס
</button>
</tbody>

{{#שאלה 4}}
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
{{/שאלה 4}}

</tbody>
{{#תשובה 4}}
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
{{/תשובה 4}}

</tbody>
{{#שאלה 5}}
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
{{/שאלה 5}}

</tbody>
{{#תשובה 5}}
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
{{/תשובה 5}}

</tbody>
{{#שאלה 6}}
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
{{/שאלה 6}}

</tbody>
{{#תשובה 6}}
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
{{/תשובה 6}}

</tbody>
{{#שאלה 7}}
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
{{/שאלה 7}}
</tbody>
{{#תשובה 7}}
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
{{/תשובה 7}}
</tbody>
{{#שאלה 8}}
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
{{/שאלה 8}}
</tbody>
{{#תשובה 8}}
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
{{/תשובה 8}}
</tbody>
{{#שאלה 9}}
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
{{/שאלה 9}}
</tbody>
{{#תשובה 9}}
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
{{/תשובה 9}}
</tbody>
{{#שאלה 10}}
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
{{/שאלה 10}}
</tbody>
{{#תשובה 10}}
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
{{/תשובה 10}}
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
 console.log(error)
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
 console.log(error)
 }

 }
 window.pycmd("hide!:all")
 }
 hideall()
</script>
"""
card4_front = """
{{#שאלה 4}}
 <div style='font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
 שאלה
 </div>
 <table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
 <tbody >
 <tr>
 <td class = "colors" style="; border-radius: 5px; ">
 <span style=" font-weight: bold; ">{{#מקור}}{{edit:מקור}}{{/מקור}}</span>
 {{#שאלה 1}}{{edit:שאלה 1}}{{/שאלה 1}}
 <div style='font-family: livorna ; font-size: 20px; color: blue;'>{{#רמז}}{{edit:hint:רמז}}{{/רמז}}</div>

 </td>

 </tr>
 </tbody>

 </table>
 <br>

</tbody>
{{#תשובה 1}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 1}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 1}}
{{#שאלה 2}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 2}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 2}}

</tbody>
{{#תשובה 2}}

<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 2}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 2}}
{{#שאלה 3}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 3}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 3}}

</tbody>
{{#תשובה 3}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 3}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 3}}
{{#שאלה 4}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 4}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 4}}
</tbody>

{{/שאלה 4}}
"""

card4_back = """
{{FrontSide}}

<hr id=answer>
<div style='font-family: livorna ; font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
 תשובה
</div>
</tbody>

{{#תשובה 4}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 4}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 4}}

<button onclick=showall()>
 ווייזט אלעס
</button>
<button onclick=hideall()>
 באהאלט אלעס
</button>

</tbody>
{{#שאלה 5}}
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
{{/שאלה 5}}

</tbody>
{{#תשובה 5}}
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
{{/תשובה 5}}

</tbody>
{{#שאלה 6}}
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
{{/שאלה 6}}

</tbody>
{{#תשובה 6}}
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
{{/תשובה 6}}

</tbody>
{{#שאלה 7}}
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
{{/שאלה 7}}
</tbody>
{{#תשובה 7}}
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
{{/תשובה 7}}
</tbody>
{{#שאלה 8}}
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
{{/שאלה 8}}
</tbody>
{{#תשובה 8}}
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
{{/תשובה 8}}
</tbody>
{{#שאלה 9}}
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
{{/שאלה 9}}
</tbody>
{{#תשובה 9}}
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
{{/תשובה 9}}
</tbody>
{{#שאלה 10}}
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
{{/שאלה 10}}
</tbody>
{{#תשובה 10}}
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
{{/תשובה 10}}
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
 console.log(error)
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
 console.log(error)
 }

 }
 window.pycmd("hide!:all")
 }
 hideall()
</script>
"""
card5_front = """
{{#שאלה 5}}
 <div style='font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
 שאלה
 </div>
 <table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
 <tbody >
 <tr>
 <td class = "colors" style="; border-radius: 5px; ">
 <span style=" font-weight: bold; ">{{#מקור}}{{edit:מקור}}{{/מקור}}</span>
 {{#שאלה 1}}{{edit:שאלה 1}}{{/שאלה 1}}
 <div style='font-family: livorna ; font-size: 20px; color: blue;'>{{#רמז}}{{edit:hint:רמז}}{{/רמז}}</div>

 </td>

 </tr>
 </tbody>

 </table>
 <br>

</tbody>
{{#תשובה 1}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 1}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 1}}
{{#שאלה 2}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 2}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 2}}

</tbody>
{{#תשובה 2}}

<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 2}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 2}}
{{#שאלה 3}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 3}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 3}}

</tbody>
{{#תשובה 3}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 3}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 3}}
{{#שאלה 4}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 4}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 4}}
{{#תשובה 4}}
</tbody>

<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 4}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 4}}
{{#שאלה 5}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 5}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 5}}
</tbody>

{{/שאלה 5}}
"""

card5_back = """
{{FrontSide}}

<hr id=answer>
<div style='font-family: livorna ; font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
 תשובה
</div>
</tbody>

{{#תשובה 5}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 5}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 5}}

<button onclick=showall()>
 ווייזט אלעס
</button>
<button onclick=hideall()>
 באהאלט אלעס
</button>

</tbody>
{{#שאלה 6}}
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
{{/שאלה 6}}

</tbody>
{{#תשובה 6}}
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
{{/תשובה 6}}

</tbody>
{{#שאלה 7}}
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
{{/שאלה 7}}
</tbody>
{{#תשובה 7}}
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
{{/תשובה 7}}
</tbody>
{{#שאלה 8}}
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
{{/שאלה 8}}
</tbody>
{{#תשובה 8}}
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
{{/תשובה 8}}
</tbody>
{{#שאלה 9}}
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
{{/שאלה 9}}
</tbody>
{{#תשובה 9}}
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
{{/תשובה 9}}
</tbody>
{{#שאלה 10}}
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
{{/שאלה 10}}
</tbody>
{{#תשובה 10}}
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
{{/תשובה 10}}
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
 console.log(error)
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
 console.log(error)
 }

 }
 window.pycmd("hide!:all")
 }
 hideall()
</script>
"""
card6_front = """
{{#שאלה 6}}
 <div style='font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
 שאלה
 </div>
 <table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
 <tbody >
 <tr>
 <td class = "colors" style="; border-radius: 5px; ">
 <span style=" font-weight: bold; ">{{#מקור}}{{edit:מקור}}{{/מקור}}</span>
 {{#שאלה 1}}{{edit:שאלה 1}}{{/שאלה 1}}
 <div style='font-family: livorna ; font-size: 20px; color: blue;'>{{#רמז}}{{edit:hint:רמז}}{{/רמז}}</div>

 </td>

 </tr>
 </tbody>

 </table>
 <br>

</tbody>
{{#תשובה 1}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 1}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 1}}
{{#שאלה 2}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 2}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 2}}

</tbody>
{{#תשובה 2}}

<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 2}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 2}}
{{#שאלה 3}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 3}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 3}}

</tbody>
{{#תשובה 3}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 3}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 3}}
{{#שאלה 4}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 4}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 4}}
{{#תשובה 4}}
</tbody>

<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 4}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 4}}
{{#שאלה 5}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 5}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 5}}

</tbody>
{{#תשובה 5}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 5}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 5}}
{{#שאלה 6}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 6}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 6}}

</tbody>

{{/שאלה 6}}
"""

card6_back = """
{{FrontSide}}

<hr id=answer>
<div style='font-family: livorna ; font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
 תשובה
</div>
</tbody>

{{#תשובה 6}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 6}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 6}}

<button onclick=showall()>
 ווייזט אלעס
</button>
<button onclick=hideall()>
 באהאלט אלעס
</button>

</tbody>
{{#שאלה 7}}
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
{{/שאלה 7}}
</tbody>
{{#תשובה 7}}
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
{{/תשובה 7}}
</tbody>
{{#שאלה 8}}
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
{{/שאלה 8}}
</tbody>
{{#תשובה 8}}
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
{{/תשובה 8}}
</tbody>
{{#שאלה 9}}
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
{{/שאלה 9}}
</tbody>
{{#תשובה 9}}
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
{{/תשובה 9}}
</tbody>
{{#שאלה 10}}
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
{{/שאלה 10}}
</tbody>
{{#תשובה 10}}
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
{{/תשובה 10}}
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
 console.log(error)
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
 console.log(error)
 }

 }
 window.pycmd("hide!:all")
 }
 hideall()
</script>
"""
card7_front = """
{{#שאלה 7}}
 <div style='font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
 שאלה
 </div>
 <table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
 <tbody >
 <tr>
 <td class = "colors" style="; border-radius: 5px; ">
 <span style=" font-weight: bold; ">{{#מקור}}{{edit:מקור}}{{/מקור}}</span>
 {{#שאלה 1}}{{edit:שאלה 1}}{{/שאלה 1}}
 <div style='font-family: livorna ; font-size: 20px; color: blue;'>{{#רמז}}{{edit:hint:רמז}}{{/רמז}}</div>

 </td>

 </tr>
 </tbody>

 </table>
 <br>

</tbody>
{{#תשובה 1}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 1}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 1}}
{{#שאלה 2}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 2}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 2}}

</tbody>
{{#תשובה 2}}

<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 2}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 2}}
{{#שאלה 3}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 3}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 3}}

</tbody>
{{#תשובה 3}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 3}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 3}}
{{#שאלה 4}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 4}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 4}}
{{#תשובה 4}}
</tbody>

<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 4}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 4}}
{{#שאלה 5}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 5}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 5}}

</tbody>
{{#תשובה 5}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 5}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 5}}
{{#שאלה 6}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 6}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 6}}

</tbody>
{{#תשובה 6}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 6}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 6}}
{{#שאלה 7}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 7}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 7}}
</tbody>

{{/שאלה 7}}
"""

card7_back = """
{{FrontSide}}

<hr id=answer>
<div style='font-family: livorna ; font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
 תשובה
</div>
</tbody>

{{#תשובה 7}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 7}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 7}}

<button onclick=showall()>
 ווייזט אלעס
</button>
<button onclick=hideall()>
 באהאלט אלעס
</button>
</tbody>
{{#שאלה 8}}
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
{{/שאלה 8}}
</tbody>
{{#תשובה 8}}
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
{{/תשובה 8}}
</tbody>
{{#שאלה 9}}
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
{{/שאלה 9}}
</tbody>
{{#תשובה 9}}
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
{{/תשובה 9}}
</tbody>
{{#שאלה 10}}
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
{{/שאלה 10}}
</tbody>
{{#תשובה 10}}
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
{{/תשובה 10}}
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
 console.log(error)
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
 console.log(error)
 }

 }
 window.pycmd("hide!:all")
 }
 hideall()
</script>
"""
card8_front = """
{{#שאלה 8}}
 <div style='font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
 שאלה
 </div>
 <table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
 <tbody >
 <tr>
 <td class = "colors" style="; border-radius: 5px; ">
 <span style=" font-weight: bold; ">{{#מקור}}{{edit:מקור}}{{/מקור}}</span>
 {{#שאלה 1}}{{edit:שאלה 1}}{{/שאלה 1}}
 <div style='font-family: livorna ; font-size: 20px; color: blue;'>{{#רמז}}{{edit:hint:רמז}}{{/רמז}}</div>

 </td>

 </tr>
 </tbody>

 </table>
 <br>

</tbody>
{{#תשובה 1}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 1}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 1}}
{{#שאלה 2}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 2}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 2}}

</tbody>
{{#תשובה 2}}

<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 2}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 2}}
{{#שאלה 3}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 3}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 3}}

</tbody>
{{#תשובה 3}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 3}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 3}}
{{#שאלה 4}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 4}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 4}}
{{#תשובה 4}}
</tbody>

<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 4}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 4}}
{{#שאלה 5}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 5}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 5}}

</tbody>
{{#תשובה 5}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 5}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 5}}
{{#שאלה 6}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 6}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 6}}

</tbody>
{{#תשובה 6}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 6}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 6}}
{{#שאלה 7}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 7}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 7}}

</tbody>
{{#תשובה 7}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 7}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 7}}
{{#שאלה 8}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 8}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 8}}

</tbody>

{{/שאלה 8}}
"""

card8_back = """
{{FrontSide}}

<hr id=answer>
<div style='font-family: livorna ; font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
 תשובה
</div>
</tbody>

{{#תשובה 8}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 8}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 8}}

<button onclick=showall()>
 ווייזט אלעס
</button>
<button onclick=hideall()>
 באהאלט אלעס
</button>
</tbody>
{{#שאלה 9}}
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
{{/שאלה 9}}
</tbody>
{{#תשובה 9}}
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
{{/תשובה 9}}
</tbody>
{{#שאלה 10}}
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
{{/שאלה 10}}
</tbody>
{{#תשובה 10}}
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
{{/תשובה 10}}
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
 console.log(error)
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
 console.log(error)
 }

 }
 window.pycmd("hide!:all")
 }
 hideall()
</script>
"""
card9_front = """
{{#שאלה 9}}
 <div style='font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
 שאלה
 </div>
 <table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
 <tbody >
 <tr>
 <td class = "colors" style="; border-radius: 5px; ">
 <span style=" font-weight: bold; ">{{#מקור}}{{edit:מקור}}{{/מקור}}</span>
 {{#שאלה 1}}{{edit:שאלה 1}}{{/שאלה 1}}
 <div style='font-family: livorna ; font-size: 20px; color: blue;'>{{#רמז}}{{edit:hint:רמז}}{{/רמז}}</div>

 </td>

 </tr>
 </tbody>

 </table>
 <br>

</tbody>
{{#תשובה 1}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 1}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 1}}
{{#שאלה 2}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 2}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 2}}

</tbody>
{{#תשובה 2}}

<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 2}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 2}}
{{#שאלה 3}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 3}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 3}}

</tbody>
{{#תשובה 3}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 3}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 3}}
{{#שאלה 4}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 4}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 4}}
{{#תשובה 4}}
</tbody>

<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 4}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 4}}
{{#שאלה 5}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 5}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 5}}

</tbody>
{{#תשובה 5}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 5}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 5}}
{{#שאלה 6}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 6}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 6}}

</tbody>
{{#תשובה 6}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 6}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 6}}
{{#שאלה 7}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 7}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 7}}

</tbody>
{{#תשובה 7}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 7}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 7}}
{{#שאלה 8}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 8}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 8}}

</tbody>
{{#תשובה 8}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 8}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 8}}
{{#שאלה 9}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 9}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 9}}

</tbody>

<!-- #355 — הוסרו כאן שני בלוקים שהיו קיימים רק בכרטיס 9 (בהשוואה לכל שאר הכרטיסים 1-8):
     1) {{#תשובה 9}} — חשף את התשובה של הכרטיס הנוכחי עצמו כבר בחזית, לפני "ווייזט די תשובה".
        card8 למשל עוצר אחרי הצגת השאלה שלו ולא חושף את תשובתו-שלו. card9_back כבר
        מציג את תשובה 9 כראוי אחרי הפרדת "תשובה" — זה בדיוק מה שגרם לכפילות המדויקת
        שנראתה בתמונה: אותו טקסט תשובה מופיע פעמיים ברצף.
     2) {{#שאלה 10}} ללא הסתרה (id=q10/hidden) — חשף את שאלה 10 ישירות בחזית, לפני
        לחיצת "ווייזט שאלה 10", בעוד card9_back מציג אותה כראוי מאחורי כפתור נסתר. -->

</tbody>

{{/שאלה 9}}
"""

card9_back = """
{{FrontSide}}

<hr id=answer>
<div style='font-family: livorna ; font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
 תשובה
</div>
</tbody>

{{#תשובה 9}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 9}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 9}}

<button onclick=showall()>
 ווייזט אלעס
</button>
<button onclick=hideall()>
 באהאלט אלעס
</button>
</tbody>

</tbody>
{{#שאלה 10}}
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
{{/שאלה 10}}
</tbody>
{{#תשובה 10}}
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
{{/תשובה 10}}
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
 console.log(error)
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
 console.log(error)
 }

 }
 window.pycmd("hide!:all")
 }
 hideall()
</script>
"""
card10_front = """
{{#שאלה 10}}
 <div style='font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
 שאלה
 </div>
 <table style= " width: 100%; " border="0"
 cellpadding="10" cellspacing="10">
 <tbody >
 <tr>
 <td class = "colors" style="; border-radius: 5px; ">
 <span style=" font-weight: bold; ">{{#מקור}}{{edit:מקור}}{{/מקור}}</span>
 {{#שאלה 1}}{{edit:שאלה 1}}{{/שאלה 1}}
 <div style='font-family: livorna ; font-size: 20px; color: blue;'>{{#רמז}}{{edit:hint:רמז}}{{/רמז}}</div>

 </td>

 </tr>
 </tbody>

 </table>
 <br>

</tbody>
{{#תשובה 1}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 1}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 1}}
{{#שאלה 2}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 2}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 2}}

</tbody>
{{#תשובה 2}}

<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 2}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 2}}
{{#שאלה 3}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 3}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 3}}

</tbody>
{{#תשובה 3}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 3}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 3}}
{{#שאלה 4}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 4}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 4}}
{{#תשובה 4}}
</tbody>

<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 4}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 4}}
{{#שאלה 5}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 5}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 5}}

</tbody>
{{#תשובה 5}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 5}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 5}}
{{#שאלה 6}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 6}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 6}}

</tbody>
{{#תשובה 6}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 6}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 6}}
{{#שאלה 7}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 7}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 7}}

</tbody>
{{#תשובה 7}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 7}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 7}}
{{#שאלה 8}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 8}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 8}}

</tbody>
{{#תשובה 8}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 8}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 8}}
{{#שאלה 9}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 9}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 9}}

</tbody>

{{#תשובה 9}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; ">{{edit:תשובה 9}}</td>
 </tr>
 </tbody>

</table>
{{/תשובה 9}}
{{#שאלה 10}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " >{{edit:שאלה 10}}</td>
 </tr>
 </tbody>

</table>
{{/שאלה 10}}

</tbody>

{{/שאלה 10}}
"""

card10_back = """
{{FrontSide}}

<hr id=answer>
<div style='font-family: livorna ; font-family: livorna; font-size: 20px; font-weight: bold;text-align:center '>
 תשובה
</div>
</tbody>

{{#תשובה 10}}
<table style=" width: 100%;" border="0" cellpadding="10" cellspacing="10">
 <tbody>
 <tr>
 <td class="colors" style=" border-radius: 5px; " id=a10>{{edit:תשובה 10}}</td>
 </tr>
 </tbody>

</table>

{{/תשובה 10}}
"""

card_css = """

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

few_q_sep_cards_model = "07 ווי 06: יעדע שאלה אלס המשך און אויך אלס באזונדער קארטל (ביז 10 קארטלעך)"
few_q_sep_cards_cards = {"card1":
 {
 "card_name": "שאלה 1 - עטליכע שאלות און תשובות; יעדער שטאפל אויך באזונדער",
 "card_front": card1_front,
 "card_back": card1_back,
 "card_css": card_css
 },
"card2":
 {
 "card_name": "שאלה 2 - עטליכע שאלות און תשובות; יעדער שטאפל אויך באזונדער",
 "card_front": card2_front,
 "card_back": card2_back,
 "card_css": card_css
 },
"card3":
 {
 "card_name": "שאלה 3 - עטליכע שאלות און תשובות; יעדער שטאפל אויך באזונדער",
 "card_front": card3_front,
 "card_back": card3_back,
 "card_css": card_css
 },
"card4":
 {
 "card_name": "שאלה 4 - עטליכע שאלות און תשובות; יעדער שטאפל אויך באזונדער",
 "card_front": card4_front,
 "card_back": card4_back,
 "card_css": card_css
 },
"card5":
 {
 "card_name": "שאלה 5 - עטליכע שאלות און תשובות; יעדער שטאפל אויך באזונדער",
 "card_front": card5_front,
 "card_back": card5_back,
 "card_css": card_css
 },
"card6":
 {
 "card_name": "שאלה 6 - עטליכע שאלות און תשובות; יעדער שטאפל אויך באזונדער",
 "card_front": card6_front,
 "card_back": card6_back,
 "card_css": card_css
 },
"card7":
 {
 "card_name": "שאלה 7 - עטליכע שאלות און תשובות; יעדער שטאפל אויך באזונדער",
 "card_front": card7_front,
 "card_back": card7_back,
 "card_css": card_css
 },
"card8":
 {
 "card_name": "שאלה 8 - עטליכע שאלות און תשובות; יעדער שטאפל אויך באזונדער",
 "card_front": card8_front,
 "card_back": card8_back,
 "card_css": card_css
 },
"card9":
 {
 "card_name": "שאלה 9 - עטליכע שאלות און תשובות; יעדער שטאפל אויך באזונדער",
 "card_front": card9_front,
 "card_back": card9_back,
 "card_css": card_css
 },
"card10":
 {
 "card_name": "שאלה 10 - עטליכע שאלות און תשובות; יעדער שטאפל אויך באזונדער",
 "card_front": card10_front,
 "card_back": card10_back,
 "card_css": card_css
 }
}
few_q_sep_cards_fields = {
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
few_q_sep_cards_type = {
 "type": 0,
}
