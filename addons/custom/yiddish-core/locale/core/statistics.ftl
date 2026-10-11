statistics-due-date = חזרה־דאטום
statistics-due-count = גרייט צו חזרה
statistics-due-for-new-card = נייע #{ $number }
statistics-cards-per-min = { $cards-per-minute } קארטלעך/מינוט
statistics-average-answer-time = { $average-seconds }ס ({ statistics-cards-per-min })
statistics-in-time-span-seconds =
    { $amount ->
        [one] אין { $amount } סעקונדע
       *[other] אין { $amount } סעקונדעס
    }
statistics-in-time-span-minutes =
    { $amount ->
        [one] אין { $amount } מינוט
       *[other] אין { $amount } מינוטן
    }
statistics-in-time-span-hours =
    { $amount ->
        [one] אין { $amount } שעה
       *[other] אין { $amount } שעה'ן
    }
statistics-in-time-span-days =
    { $amount ->
        [one] אין { $amount } טאג
       *[other] אין { $amount } טעג
    }
statistics-in-time-span-months =
    { $amount ->
        [one] אין { $amount } חודש
       *[other] אין { $amount } חדשים
    }
statistics-in-time-span-years =
    { $amount ->
        [one] אין { $amount } יאר
       *[other] אין { $amount } יאר
    }
statistics-studied-today =
    היינט געלערנט { statistics-cards }
    { $unit ->
        [seconds] { statistics-in-time-span-seconds }
        [minutes] { statistics-in-time-span-minutes }
        [hours] { statistics-in-time-span-hours }
        [days] { statistics-in-time-span-days }
        [months] { statistics-in-time-span-months }
       *[years] { statistics-in-time-span-years }
    }
    ({ $secs-per-card }ס/קארטל)
statistics-cards =
    { $cards ->
        [one] { $cards } קארטל
       *[other] { $cards } קארטלעך
    }
statistics-notes =
    { $notes ->
        [one] { $notes } רשומה
       *[other] { $notes } רשומות
    }
statistics-reviews =
    { $reviews ->
        [one] { $reviews } חזרה
       *[other] { $reviews } חזרות
    }
statistics-memorized = {$memorized} קארטלעך אין זכרון
statistics-today-title = היינט
statistics-today-again-count = צאל נאכאמאל:
statistics-today-type-counts = לערנען: { $learnCount }, חזרה: { $reviewCount }, איבערלערנען: { $relearnCount }, געפילטערט: { $filteredCount }
statistics-today-no-cards = קיין קארטלעך זענען נישט געלערנט געווארן היינט.
statistics-today-no-mature-cards = קיין באפעסטיגטע קארטלעך זענען נישט געלערנט געווארן היינט.
statistics-today-correct-mature = ריכטיגע ענטפערס אויף באפעסטיגטע קארטלעך: { $correct }/{ $total } ({ $percent }%)
statistics-counts-total-cards = אין גאנצן
statistics-counts-new-cards = נייע
statistics-counts-young-cards = פרישע
statistics-counts-mature-cards = באפעסטיגטע
statistics-counts-suspended-cards = אפגעשטעלטע
statistics-counts-buried-cards = באזייטיגטע
statistics-counts-filtered-cards = געפילטערטע
statistics-counts-learning-cards = ביים לערנען
statistics-counts-relearning-cards = ביים איבערלערנען
statistics-counts-title = צאל קארטלעך
statistics-counts-separate-suspended-buried-cards = צעטיילן אפגעשטעלטע/באזייטיגטע קארטלעך
statistics-true-retention-title = געדענק־ראטע
statistics-true-retention-subtitle = הצלחה־ראטע ביי קארטלעך מיט אן אפשטאנד ≥ 1 טאג.
statistics-true-retention-tooltip = אויב איר נוצט FSRS, זאל אייער געדענק־ראטע זיין נאענט צום געוואונטשענעם ווערט. דאטן פון איין טאג שוואנקען שטארק, דעריבער איז בעסער צו קוקן אויף חודש'ליכע דאטן.
statistics-true-retention-range = תקופה
statistics-true-retention-pass = געוואוסט
statistics-true-retention-fail = פארגעסן
statistics-true-retention-total = אין גאנצן
statistics-true-retention-count = צאל
statistics-true-retention-retention = געדענק־ראטע
statistics-true-retention-young = פרישע
statistics-true-retention-mature = באפעסטיגטע
statistics-true-retention-all = אלע
statistics-true-retention-today = היינט
statistics-true-retention-yesterday = נעכטן
statistics-true-retention-week = לעצטע וואך
statistics-true-retention-month = לעצטע חודש
statistics-true-retention-year = לעצטע יאר
statistics-true-retention-all-time = די גאנצע צייט
statistics-true-retention-not-applicable = נישט פארהאן
statistics-range-all-time = אלע
statistics-range-1-year-history = לעצטע 12 חדשים
statistics-range-all-history = גאנצע היסטאריע
statistics-range-deck = פעקל
statistics-range-collection = זאמלונג
statistics-range-search = זוכן
statistics-card-ease-title = קארטל־גרינגקייט
statistics-card-difficulty-title = קארטל־שוועריגקייט
statistics-card-stability-title = קארטל־פעסטקייט
statistics-card-stability-subtitle = דער אפשטאנד ביז דער שאנס צו געדענקען פאלט צו 90%.
statistics-median-stability = מיטלווערדיגע פעסטקייט
statistics-card-retrievability-title = שאנס צו געדענקען קארטלעך
statistics-card-ease-subtitle = וואס נידריגער די גרינגקייט, אלץ אפטער וועט דער קארטל ערשיינען.
statistics-card-difficulty-subtitle2 = וואס העכער די שוועריגקייט, אלץ לאנגזאמער וועט די פעסטקייט וואקסן.
statistics-retrievability-subtitle = דער שאנס צו געדענקען א קארטל היינט.
statistics-card-ease-tooltip =
    { $cards ->
        [one] { $cards } קארטל מיט { $percent } גרינגקייט
       *[other] { $cards } קארטלעך מיט { $percent } גרינגקייט
    }
statistics-card-difficulty-tooltip =
    { $cards ->
        [one] { $cards } קארטל מיט { $percent } שוועריגקייט
       *[other] { $cards } קארטלעך מיט { $percent } שוועריגקייט
    }
statistics-retrievability-tooltip =
    { $cards ->
        [one] { $cards } קארטל מיט { $percent } שאנס צו געדענקען
       *[other] { $cards } קארטלעך מיט { $percent } שאנס צו געדענקען
    }
statistics-future-due-title = קומענדיגע חזרות
statistics-future-due-subtitle = די צאל חזרות וואס וועלן זיין גרייט אין דער צוקונפט.
statistics-added-title = צוגעלייגט
statistics-added-subtitle = די צאל נייע קארטלעך וואס איר האט צוגעלייגט.
statistics-reviews-count-subtitle = די צאל פראגעס וואס איר האט געענטפערט.
statistics-reviews-time-subtitle = די צייט וואס עס האט גענומען צו ענטפערן די פראגעס.
statistics-answer-buttons-title = ענטפער־קנעפלעך
statistics-answer-buttons-button-number = קנעפל
statistics-answer-buttons-button-pressed = מאל געדריקט
statistics-answer-buttons-subtitle = וויפיל מאל איר האט געדריקט יעדן קנעפל.
statistics-reviews-title = חזרות
statistics-reviews-time-checkbox = צייט
statistics-in-days-single =
    { $days ->
        [0] היינט
        [1] מארגן
       *[other] אין { $days } טעג
    }
statistics-in-days-range = אין { $daysStart }-{ $daysEnd } טעג
statistics-days-ago-single =
    { $days ->
        [1] נעכטן
       *[other] פאר { $days } טעג
    }
statistics-days-ago-range = פאר { $daysStart }-{ $daysEnd } טעג
statistics-running-total = צוזאמענגעציילט
statistics-cards-due =
    { $cards ->
        [one] { $cards } קארטל גרייט צו חזרה
       *[other] { $cards } קארטלעך גרייט צו חזרה
    }
statistics-backlog-checkbox = פארשפעטיגטע
statistics-intervals-title = חזרה־אפשטאנדן
statistics-intervals-subtitle = אפשטאנדן ביז חזרה־קארטלעך ווערן נאכאמאל געוויזן.
statistics-intervals-day-range =
    { $cards ->
        [one] { $cards } קארטל מיט אן אפשטאנד פון { $daysStart }~{ $daysEnd } טעג
       *[other] { $cards } קארטלעך מיט אן אפשטאנד פון { $daysStart }~{ $daysEnd } טעג
    }
statistics-intervals-day-single =
    { $cards ->
        [one] { $cards } קארטל מיט אן אפשטאנד פון { $day } טעג
       *[other] { $cards } קארטלעך מיט אן אפשטאנד פון { $day } טעג
    }
statistics-stability-day-range =
    { $cards ->
        [one] { $cards } קארטל מיט א פעסטקייט פון { $daysStart }~{ $daysEnd } טעג
       *[other] { $cards } קארטלעך מיט א פעסטקייט פון { $daysStart }~{ $daysEnd } טעג
    }
statistics-stability-day-single =
    { $cards ->
        [one] { $cards } קארטל מיט א פעסטקייט פון { $day } טעג
       *[other] { $cards } קארטלעך מיט א פעסטקייט פון { $day } טעג
    }
statistics-hours-range = פון { $hourStart }:00~{ $hourEnd }:00
statistics-hours-correct = { $correct }/{ $total } ריכטיג ({ $percent }%)
statistics-hours-correct-info = → (נישט 'נאכאמאל')
statistics-hours-reviews = 📊 { $reviews } חזרות
statistics-hours-correct-reviews = 📈 { $percent }% ריכטיג ({ $reviews })
statistics-hours-title = צעטיילונג לויט שעה
statistics-hours-subtitle = הצלחה־ראטע פון חזרות פאר יעדע שעה פונעם טאג.
statistics-no-data = נישטא קיין דאטן
statistics-calendar-title = קאלענדאר
statistics-elapsed-time-seconds = { $amount }ס
statistics-elapsed-time-minutes = { $amount }מ
statistics-elapsed-time-hours = { $amount }ש
statistics-elapsed-time-days = { $amount }ט
statistics-elapsed-time-months = { $amount }חד
statistics-elapsed-time-years = { $amount }י
statistics-average-for-days-studied = דורכשניט פאר טעג וואס מען האט געלערנט
statistics-total = אין גאנצן
statistics-days-studied = טעג געלערנט
statistics-average-answer-time-label = דורכשניטליכע ענטפער־צייט
statistics-average = דורכשניט
statistics-median-interval = מיטלווערדיגער אפשטאנד
statistics-due-tomorrow = גרייט מארגן
statistics-daily-load = טעגליכע ארבעט
statistics-amount-of-total-with-percentage = { $amount } פון { $total } ({ $percent }%)
statistics-average-over-period = דורכשניט איבער דער תקופה
statistics-reviews-per-day =
    { $count ->
        [one] { $count } חזרה/טאג
       *[other] { $count } חזרות/טאג
    }
statistics-minutes-per-day =
    { $count ->
        [one] { $count } מינוט/טאג
       *[other] { $count } מינוטן/טאג
    }
statistics-cards-per-day =
    { $count ->
        [one] { $count } קארטל/טאג
       *[other] { $count } קארטלעך/טאג
    }
statistics-median-ease = מיטלווערדיגע גרינגקייט
statistics-median-difficulty = מיטלווערדיגע שוועריגקייט
statistics-average-retrievability = דורכשניטליכער שאנס צו געדענקען
statistics-estimated-total-knowledge = געשאצטע גאנצע קענטעניש
statistics-save-pdf = אפזיכערן PDF
statistics-saved = אפגעזיכערט.
statistics-stats = סטאטיסטיק
statistics-title = סטאטיסטיק
statistics-average-stability = דורכשניטליכע פעסטקייט
statistics-average-interval = דורכשניטליכער אפשטאנד
statistics-average-ease = דורכשניטליכע גרינגקייט
statistics-average-difficulty = דורכשניטליכע שוועריגקייט
