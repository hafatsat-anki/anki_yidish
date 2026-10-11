"""
Manages note type and templates
"""



card1_front = """
<script>
    // Loading Persistence
    // https://github.com/SimonLammer/anki-persistence
    // v0.5.2 - https://github.com/SimonLammer/anki-persistence/blob/62463a7f63e79ce12f7a622a8ca0beb4c1c5d556/script.js
    if (void 0 === window.Persistence) { var _persistenceKey = "github.com/SimonLammer/anki-persistence/", _defaultKey = "_default"; if (window.Persistence_sessionStorage = function () { var e = !1; try { "object" == typeof window.sessionStorage && (e = !0, this.clear = function () { for (var e = 0; e < sessionStorage.length; e++) { var t = sessionStorage.key(e); 0 == t.indexOf(_persistenceKey) && (sessionStorage.removeItem(t), e--) } }, this.setItem = function (e, t) { void 0 == t && (t = e, e = _defaultKey), sessionStorage.setItem(_persistenceKey + e, JSON.stringify(t)) }, this.getItem = function (e) { return void 0 == e && (e = _defaultKey), JSON.parse(sessionStorage.getItem(_persistenceKey + e)) }, this.removeItem = function (e) { void 0 == e && (e = _defaultKey), sessionStorage.removeItem(_persistenceKey + e) }) } catch (e) { } this.isAvailable = function () { return e } }, window.Persistence_windowKey = function (e) { var t = window[e], i = !1; "object" == typeof t && (i = !0, this.clear = function () { t[_persistenceKey] = {} }, this.setItem = function (e, i) { void 0 == i && (i = e, e = _defaultKey), t[_persistenceKey][e] = i }, this.getItem = function (e) { return void 0 == e && (e = _defaultKey), t[_persistenceKey][e] || null }, this.removeItem = function (e) { void 0 == e && (e = _defaultKey), delete t[_persistenceKey][e] }, void 0 == t[_persistenceKey] && this.clear()), this.isAvailable = function () { return i } }, window.Persistence = new Persistence_sessionStorage, Persistence.isAvailable() || (window.Persistence = new Persistence_windowKey("py")), !Persistence.isAvailable()) { var titleStartIndex = window.location.toString().indexOf("title"), titleContentIndex = window.location.toString().indexOf("main", titleStartIndex); titleStartIndex > 0 && titleContentIndex > 0 && titleContentIndex - titleStartIndex < 10 && (window.Persistence = new Persistence_windowKey("qt")) } }
</script>

{{#כותרת}}<h3 id="myH1">{{כותרת}}</h3>{{/כותרת}}
{{#שאלה}}<p>{{שאלה}}</p>{{/שאלה}}

<table style="border: 1px solid black" id="qtable"></table>\

<div class="hidden" id="Q_solutions">{{תשובות נכונות (יש להזין את מספר או מספרי התשובות הנכונות)}}</div>
<div class="hidden" id="user_answers">- - - -</div>
<div class="hidden" id="Card_Type">{{הזן את סוג השאלה (0=נכון או לא נכון,1=סמן תשובות נכונות, 2=סמן תשובה נכונה)}}</div>

<div class="hidden" id="Q_1">{{תשובה 1}}</div>
<div class="hidden" id="Q_2">{{תשובה 2}}</div>
<div class="hidden" id="Q_3">{{תשובה 3}}</div>
<div class="hidden" id="Q_4">{{תשובה 4}}</div>
<div class="hidden" id="Q_5">{{תשובה 5}}</div>

<script>
    // Generate the table depending on the type.
    function generateTable() {
        var type = document.getElementById("Card_Type").innerHTML;
        var table = document.createElement("table");
        var tbody = document.createElement("tbody");
        for (var i = 0; true; i++) {
            if (type == 0 && i == 0) {
                tbody.innerHTML = tbody.innerHTML + '<tr><th>נכון</th><th>לא נכון</th><th></th></tr>';
            }
            if (document.getElementById('Q_' + (i + 1)) != undefined) {
                if (document.getElementById('Q_' + (i + 1)).innerHTML != '') {
                    var html = [];

                    let answerText = document.getElementById('Q_' + (i + 1)).innerHTML;
                    let labelTag = (type == 0) ? '' :
                        '<label for="inputQuestion' + (i + 1) + '">' + answerText + '</label>';
                    let textAlign = (type == 0) ? 'center' : 'right';

                    html.push('<tr>');
                    var maxColumns = ((type == 0) ? 2 : 1);
                    for (var j = 0; j < maxColumns; j++) {
                        let inputTag = '<input id="inputQuestion' + (i + 1) +
                            '" name="ans_' + ((type != 2) ? (i + 1) : 'A') +
                            '" type="' + ((type == 1) ? 'checkbox' : 'radio') +
                            // TODO: I don't see how these values are used, please add a comment
                            '" value="' + ((j == 0) ? 1 : 0) + '">';
                        html.push(
                            '<td onInput="onCheck()" style="text-align: ' + textAlign + '">' + inputTag +
                            labelTag +
                            '</td>');
                    }
                    if (type == 0) {
                        html.push('<td>' + answerText + '</td>');
                    }
                    html.push('</tr>');
                    tbody.innerHTML = tbody.innerHTML + html.join("");
                }
            } else {
                break;
            }
        }

        table.appendChild(tbody);
        document.getElementById('qtable').innerHTML = table.innerHTML;
        getAns();
        onShuffle();
    }

    function shuffle(array) {
        var currentIndex = array.length, temporaryValue, randomIndex;

        // While there remain elements to shuffle...
        while (0 !== currentIndex) {

            // Pick a remaining element...
            randomIndex = Math.floor(Math.random() * currentIndex);
            currentIndex -= 1;

            // And swap it with the current element.
            temporaryValue = array[currentIndex];
            array[currentIndex] = array[randomIndex];
            array[randomIndex] = temporaryValue;
        }

        return array;
    }

    function onShuffle() {
        var solutions = document.getElementById("Q_solutions").innerHTML;
        solutions = solutions.replace(/(<([^>]+)>)/gi, "").split(" ");
        for (var i = 0; i < solutions.length; i++) {
            solutions[i] = Number(solutions[i]);
        }

        var output = document.getElementById("output");

        var qrows = document.getElementById("qtable").getElementsByTagName("tr");

        var qanda = new Array();

        var type = document.getElementById("Card_Type").innerHTML;

        for (i = 0; i < ((type == 0) ? qrows.length - 1 : qrows.length); i++) {
            qanda[i] = new Object();
            qanda[i].question = qrows[(type == 0) ? i + 1 : i].getElementsByTagName("td")[(type == 0) ? 2 : 0].innerHTML;
            qanda[i].answer = solutions[i];
        }

        qanda = shuffle(qanda);

        var mc_solutions = new String();

        for (i = 0; i < ((type == 0) ? qrows.length - 1 : qrows.length); i++) {
            qrows[(type == 0) ? i + 1 : i].getElementsByTagName("td")[(type == 0) ? 2 : 0].innerHTML = qanda[i].question;
            solutions[i] = qanda[i].answer;
            mc_solutions += qanda[i].answer + " ";
        }
        mc_solutions = mc_solutions.substring(0, mc_solutions.lastIndexOf(" "));
        document.getElementById("Q_solutions").innerHTML = mc_solutions;

        document.getElementById("qtable").HTML = qrows;
        onCheck();
    }

    function onCheck() {
        // Generate user_answers
        var type = document.getElementById("Card_Type").innerHTML;
        var qrows = document.getElementById("qtable").getElementsByTagName('tbody')[0].getElementsByTagName("tr");
        document.getElementById("user_answers").innerHTML = "";
        for (var i = 0; i < ((type == 0) ? qrows.length - 1 : qrows.length); i++) {
            var j;  // to skip the first row containing no checkboxes when type is 'kprim'
            if (type == 0) {
                j = i + 1;
            } else j = i;
            if (qrows[j].getElementsByTagName("td")[0].getElementsByTagName("input")[0].checked) {

                document.getElementById("user_answers").innerHTML += "1 ";
            } else if (type != 0 && !qrows[j].getElementsByTagName("td")[(type == 0) ? 1 : 0].getElementsByTagName("input")[0].checked) {
                document.getElementById("user_answers").innerHTML += "0 ";
            } else if (type == 0 && qrows[j].getElementsByTagName("td")[(type == 0) ? 1 : 0].getElementsByTagName("input")[0].checked) {
                document.getElementById("user_answers").innerHTML += "0 ";
            } else {
                document.getElementById("user_answers").innerHTML += "- ";
            }
        }

        document.getElementById("user_answers").innerHTML = document.getElementById("user_answers").innerHTML.trim();

        // Send Stuff to Persistence
        if (Persistence.isAvailable()) {
            Persistence.clear();
            Persistence.setItem('user_answers', document.getElementById("user_answers").innerHTML);
            Persistence.setItem('Q_solutions', document.getElementById("Q_solutions").innerHTML);
            Persistence.setItem('qtable', document.getElementById("qtable").innerHTML);
        }
    }

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    function tickCheckboxOnNumberKeyDown(event) {
        const keyName = event.key;

        let tableBody = document.getElementById("qtable").getElementsByTagName('tbody')[0];
        var tableRows = tableBody.getElementsByTagName("tr");

        if (0 < +keyName && +keyName < 10) {
            let tableData = tableRows[+keyName - 1].getElementsByTagName("td")[0];
            let tableRow = tableData.getElementsByTagName("input")[0];
            tableRow.checked = !tableRow.checked;
            onCheck();
        }
    }

    // addCheckboxTickingShortcuts is an easy approach on using only the keyboard to toggle checkboxes in mc/sc.
    //
    // Naturally the number keys are an intuitive choice here. Unfortunately anki does capture those.
    // So the workaround is to hold the (left) 'Alt' key and then type the corresponding number to toggle the row.
    function addCheckboxTickingShortcuts() {
        document.addEventListener('keydown', tickCheckboxOnNumberKeyDown, false);
    }

    function isMobile() {
        if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
            return true;
        } else {
            return false;
        }
    }

    function getAns() {
    var str = document.getElementById("Q_solutions").innerHTML;
    var ans = "";
    for (a=1;a<6;a++){
      if (str.includes(a)){
      ans = ans + "1 ";
      }
      else {
      ans = ans + "0 ";
      }
    }
    document.getElementById("Q_solutions").innerHTML = ans;
    }

    function run() {
        let DEFAULT_CARD_TYPE = 1; // for previewing the cards in "Manage Note Type..."

        if (isNaN(document.getElementById("Card_Type").innerHTML)) {
            document.getElementById("Card_Type").innerHTML = DEFAULT_CARD_TYPE;
        }

        if (document.getElementById("Card_Type").innerHTML != 0 && !isMobile()) {
            addCheckboxTickingShortcuts();
        }

        setTimeout(generateTable(), 1);
    }

    async function waitForReadyStateAndRun() {
        for (let i = 0; i < 100; i++) {
            if (document.readyState === "complete") {
                run();
                break;
            }
            console.log("Document not yet fully loaded (readyState: " + document.readyState + "). Retry in 0.1s.");
            await sleep(100);
        }
    }

    /*
    The following block is inspired by Glutanimate's Cloze Overlapper card template.
    The Cloze Overlapper card template is licensed under the CC BY-SA 4.0
    license (https://creativecommons.org/licenses/by-sa/4.0/).
    */
    if (document.readyState === "complete") {
        run();
    } else {
        waitForReadyStateAndRun();
    }
</script>\
"""

card1_back = """
<script>
    // Loading Persistence
    // https://github.com/SimonLammer/anki-persistence
    // v0.5.2 - https://github.com/SimonLammer/anki-persistence/blob/62463a7f63e79ce12f7a622a8ca0beb4c1c5d556/script.js
    if (void 0 === window.Persistence) { var _persistenceKey = "github.com/SimonLammer/anki-persistence/", _defaultKey = "_default"; if (window.Persistence_sessionStorage = function () { var e = !1; try { "object" == typeof window.sessionStorage && (e = !0, this.clear = function () { for (var e = 0; e < sessionStorage.length; e++) { var t = sessionStorage.key(e); 0 == t.indexOf(_persistenceKey) && (sessionStorage.removeItem(t), e--) } }, this.setItem = function (e, t) { void 0 == t && (t = e, e = _defaultKey), sessionStorage.setItem(_persistenceKey + e, JSON.stringify(t)) }, this.getItem = function (e) { return void 0 == e && (e = _defaultKey), JSON.parse(sessionStorage.getItem(_persistenceKey + e)) }, this.removeItem = function (e) { void 0 == e && (e = _defaultKey), sessionStorage.removeItem(_persistenceKey + e) }) } catch (e) { } this.isAvailable = function () { return e } }, window.Persistence_windowKey = function (e) { var t = window[e], i = !1; "object" == typeof t && (i = !0, this.clear = function () { t[_persistenceKey] = {} }, this.setItem = function (e, i) { void 0 == i && (i = e, e = _defaultKey), t[_persistenceKey][e] = i }, this.getItem = function (e) { return void 0 == e && (e = _defaultKey), t[_persistenceKey][e] || null }, this.removeItem = function (e) { void 0 == e && (e = _defaultKey), delete t[_persistenceKey][e] }, void 0 == t[_persistenceKey] && this.clear()), this.isAvailable = function () { return i } }, window.Persistence = new Persistence_sessionStorage, Persistence.isAvailable() || (window.Persistence = new Persistence_windowKey("py")), !Persistence.isAvailable()) { var titleStartIndex = window.location.toString().indexOf("title"), titleContentIndex = window.location.toString().indexOf("main", titleStartIndex); titleStartIndex > 0 && titleContentIndex > 0 && titleContentIndex - titleStartIndex < 10 && (window.Persistence = new Persistence_windowKey("qt")) } }
</script>

{{#כותרת}}<h3 id="myH1">{{כותרת}}</h3>{{/כותרת}}
{{#שאלה}}<p>{{שאלה}}</p>{{/שאלה}}
<table id="qtable"></table>\
<p id="output"></p>
<div class="hidden" id="MC_solutions">solutions_here</div>
<div class="hidden" id="user_answers">user_answers_here</div>
<div class="hidden" id="CardType">{{הזן את סוג השאלה (0=נכון או לא נכון,1=סמן תשובות נכונות, 2=סמן תשובה נכונה)}}</div>
<p id="canswerresult"><b>ציון: x %</b></p>
{{#מקור}}<p class="small" id="sources"><b>מקור:</b><br />{{מקור}}</p>{{/מקור}}
{{#הוספות}}<p class="small" id="extra1"><b>תוספות:</b><br />{{הוספות}}</p>{{/הוספות}}

<script>
    "use strict";

    function onLoad() {
        var colorizeqtable = false;
        var colorizeatable = true;
        var colorizefalsefalse = true;
        // Check if Persistence is recognized to prevent errors when viewing note in "Manage Note Types..."
        if (Persistence.isAvailable && Persistence.getItem('Q_solutions') !== null) {
            // Parsing solutions
            console.log(Persistence.getItem('Q_solutions'));
            var solutions = Persistence.getItem('Q_solutions').split(" ");
            for (let i = 0; i < solutions.length; i++) {
                solutions[i] = Number(solutions[i]);
            }
            var answers = Persistence.getItem('user_answers').split(" ");
            var type = document.getElementById('CardType').innerHTML;
            var qtable = document.getElementById('qtable');
            qtable.innerHTML = Persistence.getItem('qtable');
            var output = document.getElementById("output");
            var atable = qtable.cloneNode(true);
            atable.setAttribute("id", "atable");
            output.innerHTML = "<hr id='answer' />" + atable.outerHTML;
            document.getElementById('qtable').innerHTML = qtable.innerHTML;
            var qrows = qtable.getElementsByTagName('tbody')[0].getElementsByTagName("tr");

            for (let i = 0; i < answers.length; i++) {
                //Set the radio buttons in the qtable.
                if (type == 0) {
                    if (answers[i] === "1") {
                        qrows[i + 1].getElementsByTagName("td")[0].getElementsByTagName("input")[0].checked = true;
                    } else if (answers[i] === "0") {
                        qrows[i + 1].getElementsByTagName("td")[1].getElementsByTagName("input")[0].checked = true;
                    }
                } else {
                    qrows[i].getElementsByTagName("td")[0].getElementsByTagName("input")[0].checked = (answers[i] == 1) ? true : false;
                }
                //Colorize the qtable.
                if (colorizeqtable) {
                    if (solutions[i] && answers[i] === "1") {
                        qrows[(type != 0) ? i : i + 1].setAttribute("class", "correct");
                    } else if (!solutions[i] && answers[i] === "0") {
                        if (colorizefalsefalse) { qrows[(type != 0) ? i : i + 1].setAttribute("class", "correct"); }
                    } else {
                        qrows[(type != 0) ? i : i + 1].setAttribute("class", "wrong");
                    }
                }
            }

            var arows = document.getElementById("atable").getElementsByTagName("tbody")[0].getElementsByTagName("tr");
            var canswers = 0;
            for (let i = 0; i < solutions.length; i++) {
                //Rename the radio buttons of the atable to avoid interference with those in the qtable.
                if (type == 0) arows[i + 1].getElementsByTagName("td")[1].getElementsByTagName("input")[0].setAttribute("name", "ans_" + ((type != 2) ? String(i + 1) : 'A') + "_solution");
                arows[(type != 0) ? i : i + 1].getElementsByTagName("td")[0].getElementsByTagName("input")[0].setAttribute("name", "ans_" + ((type != 2) ? String(i + 1) : 'A') + "_solution");
                //Set the radio buttons in the atable.
                if (type == 0) arows[i + 1].getElementsByTagName("td")[solutions[i] ? 0 : 1].getElementsByTagName("input")[0].checked = true;
                else arows[i].getElementsByTagName("td")[0].getElementsByTagName("input")[0].checked = solutions[i] ? true : false;
                //Colorize the atable and count correct answers.
                if (colorizeatable) {
                    if (solutions[i] && answers[i] === "1") {
                        arows[(type != 0) ? i : i + 1].setAttribute("class", "correct");
                        canswers = canswers + 1;
                    } else if (!solutions[i] && answers[i] === "0") {
                        if (colorizefalsefalse) { arows[(type != 0) ? i : i + 1].setAttribute("class", "correct"); }
                        canswers = canswers + 1;
                    } else {
                        arows[(type != 0) ? i : i + 1].setAttribute("class", "wrong");
                    }
                }
            }
            var canswerresult = document.getElementById('canswerresult');
            canswerresult.innerHTML = "<b>ציון: " + Math.round(canswers / solutions.length * 100) + " %</b>";
            Persistence.clear();
        }
    }

    function isMobile() {
        if (/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
            return true;
        } else {
            return false;
        }
    }

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    function run() {
        if (!isMobile() && typeof tickCheckboxOnNumberKeyDown !== "undefined") {
            // To make sure there isn't a previously registered event handler lingering into the next review
            document.removeEventListener('keydown', tickCheckboxOnNumberKeyDown, false);
        }
        setTimeout(onLoad(), 1);
    }

    async function waitForReadyStateAndRun() {
        for (let i = 0; i < 100; i++) {
            if (document.readyState === "complete") {
                run();
                break;
            }
            console.log("Document not yet fully loaded (readyState: " + document.readyState + "). Retry in 0.1s.");
            await sleep(100);
        }
    }

    /*
    The following block is inspired by Glutanimate's Cloze Overlapper card template.
    The Cloze Overlapper card template is licensed under the CC BY-SA 4.0
    license (https://creativecommons.org/licenses/by-sa/4.0/).
    */
    if (document.readyState === "complete") {
        run();
    } else if (isMobile()) {
        document.addEventListener("DOMContentLoaded", function () {
            setTimeout(onLoad, 1);
        }, false);
    } else {
        waitForReadyStateAndRun();
    }
</script>\
"""

card1_css = """
.card {
  font-family: arial;
  font-size: 20px;
  text-align: center;
  color: black;
  background-color: white;
}

.small {
  font-size: 15px;
}

table, td, th {
  border-collapse: collapse;
  padding: 5px;
}

table {
  display: inline-block;
  text-align: left;
}

label {
  margin-left: 0.4em;
}

.correct {
  background-color: lime;
}

.nightMode .correct {
  background-color: #009900;
}

.wrong {
  background-color: OrangeRed;
}

.hidden {
  /*
  This block is from Glutanimate's Cloze Overlapper card template.
  The Cloze Overlapper card template is licensed under the CC BY-SA 4.0
  license (https://creativecommons.org/licenses/by-sa/4.0/).
  */
  /* guarantees a consistent width across front and back */
  font-weight: bold;
  display: block;
  line-height: 0;
  height: 0;
  overflow: hidden;
  visibility: hidden;
}\
"""

multi_model = "10 שאלות מיט אן אויסוואל פון תשובות (איין קארטל)"
multi_cards = {"card1":
     {
     "card_name": "שאלות מיט אן אויסוואל פון תשובות",
     "card_front": card1_front,
     "card_back": card1_back,
     "card_css": card1_css
    }
}
multi_fields = {
    "שאלה": "שאלה",
    "title": "כותרת",
    "qtype": "הזן את סוג השאלה (0=נכון או לא נכון,1=סמן תשובות נכונות, 2=סמן תשובה נכונה)",
    "q1": "תשובה 1",
    "q2": "תשובה 2",
    "q3": "תשובה 3",
    "q4": "תשובה 4",
    "q5": "תשובה 5",
    "answers": "תשובות נכונות (יש להזין את מספר או מספרי התשובות הנכונות)",
    "sources": "מקור",
    "extra": "הוספות"
}
multi_type = {
    "type": 0,
}
