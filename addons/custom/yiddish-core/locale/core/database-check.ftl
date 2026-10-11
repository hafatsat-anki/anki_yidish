database-check-corrupt = די זאמלונג־טעקע איז געשעדיגט. ביטע שטעלט צוריק פון אן אויטאמאטישן גיבוי.
database-check-rebuilt = די דאטנבאזע איז איבערגעבויט און פארבעסערט געווארן.
database-check-card-properties =
    { $count ->
        [one] { $count } אומגילטיגע קארטל־אייגנשאפט פארראכטן.
       *[other] { $count } אומגילטיגע קארטל־אייגנשאפטן פארראכטן.
    }
database-check-card-last-review-time-empty =
    { $count ->
        [one] צייט פון דער לעצטער חזרה צוגעלייגט צו { $count } קארטל.
       *[other] צייט פון דער לעצטער חזרה צוגעלייגט צו { $count } קארטלעך.
    }
database-check-missing-templates =
    { $count ->
        [one] { $count } קארטל מיט א פעלנדיגן מוסטער אויסגעמעקט.
       *[other] { $count } קארטלעך מיט פעלנדע מוסטערן אויסגעמעקט.
    }
database-check-field-count =
    { $count ->
        [one] { $count } רשומה מיט א פאלשער צאל פעלדער פארראכטן.
       *[other] { $count } רשומות מיט א פאלשער צאל פעלדער פארראכטן.
    }
database-check-new-card-high-due =
    { $count ->
        [one] געפונען { $count } נייע קארטל מיט א רייע־נומער >= 1,000,000. טראכט אים אריבעררוקן אין דורכבלעטערן.
       *[other] געפונען { $count } נייע קארטלעך מיט א רייע־נומער >= 1,000,000. טראכט זיי אריבעררוקן אין דורכבלעטערן.
    }
database-check-card-missing-note =
    { $count ->
        [one] { $count } קארטל מיט א פעלנדע רשומה אויסגעמעקט.
       *[other] { $count } קארטלעך מיט פעלנדע רשומות אויסגעמעקט.
    }
database-check-duplicate-card-ords =
    { $count ->
        [one] { $count } קארטל מיט א דאפלטן מוסטער אויסגעמעקט.
       *[other] { $count } קארטלעך מיט דאפלטע מוסטערן אויסגעמעקט.
    }
database-check-missing-decks =
    { $count ->
        [one] { $count } פעלנדע פעקל פארראכטן.
       *[other] { $count } פעלנדע פעקלעך פארראכטן.
    }
database-check-revlog-properties =
    { $count ->
        [one] { $count } חזרה־רעקארד מיט אומגילטיגע אייגנשאפטן פארראכטן.
       *[other] { $count } חזרה־רעקארדן מיט אומגילטיגע אייגנשאפטן פארראכטן.
    }
database-check-notes-with-invalid-utf8 =
    { $count ->
        [one] { $count } רשומה מיט אומגילטיגע utf8־אותיות פארראכטן.
       *[other] { $count } רשומות מיט אומגילטיגע utf8־אותיות פארראכטן.
    }
database-check-fixed-invalid-ids =
    { $count ->
        [one] { $count } אביעקט מיט צייט־שטעמפלען אין דער צוקונפט פארראכטן.
       *[other] { $count } אביעקטן מיט צייט־שטעמפלען אין דער צוקונפט פארראכטן.
    }
database-check-notetypes-recovered = איין אדער מער סארטן רשומות האבן געפעלט. די רשומות וואס האבן זיי גענוצט האבן באקומען נייע סארטן מיט נעמען וואס הייבן זיך אן מיט "db-check". די נעמען פון די פעלדער און דער קארטל־אויסשטעל זענען אבער פארלוירן געווארן, דעריבער קען זיין בעסער צוריקצושטעלן פון אן אויטאמאטישן גיבוי.
database-check-checking-integrity = מען קאנטראלירט די זאמלונג...
database-check-rebuilding = מען בויט איבער...
database-check-checking-cards = מען קאנטראלירט קארטלעך...
database-check-checking-notes = מען קאנטראלירט רשומות...
database-check-checking-history = מען קאנטראלירט היסטאריע...
database-check-title = קאנטראלירן דאטנבאזע
