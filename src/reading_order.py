import json, re

AVID = {27:"48381",28:"48382",29:"48383",30:"48384",31:"48385",32:"48386",
        33:"48387",34:"48388",35:"48389",36:"48390",37:"48391",38:"48392",
        39:"48393",40:"48394",41:"48395",42:"48396",43:"48397",44:"48398"}
SWID = {1:"52447",2:"52450",3:"52451",4:"52452",5:"52453",6:"52454",
        7:"52455",8:"52456",9:"57620"}
S_AV = "https://www.marvel.com/comics/series/16452/avengers_2012_2015"
S_NA = "https://www.marvel.com/comics/series/16451/new_avengers_2013_2015"
S_SW = "https://www.marvel.com/comics/series/19648/secret_wars_(2015_-_2016)"
S_UL = "https://www.marvel.com/comics/series/13936/ultimate_comics_ultimates_2011_2013"
S_F4 = "https://www.marvel.com/comics/series/421/fantastic_four_(1998_-_2012)"
S_FF = "https://www.marvel.com/comics/series/13440/ff_2011_2012"
S_IN = "https://www.marvel.com/comics/series/17735/infinity_(2013_-_present)"
S_SH1 = "https://www.marvel.com/comics/series/8821/shield_2010_2011"
S_SH2 = "https://www.marvel.com/comics/series/13744/shield_2011_2018"
S_WAR = "https://www.marvel.com/comics/series/6796/secret_warriors_2009_2011"
S_DRF = "https://www.marvel.com/comics/series/7000/dark_reign_fantastic_four_2009"
S_UTH = "https://www.marvel.com/comics/series/11272/ultimate_comics_thor_2010_-_2011"
S_UFA = "https://www.marvel.com/comics/series/14807/ultimate_fallout_(2011)"
S_UHA = "https://www.marvel.com/comics/series/14068/ultimate_comics_hawkeye_2011"
S_AWO = "https://www.marvel.com/comics/series/18398/avengers_world_2014_2015"
S_SIE = "https://www.marvel.com/comics/series/19608/siege_2015_-_present"
S_THO = "https://www.marvel.com/comics/series/19765/thors_2015"
S_UEN = "https://www.marvel.com/comics/series/19658/ultimate_end_2015"
I = "https://www.marvel.com/comics/issue/"
FIRST = {
 ("Secret Warriors","#1"): I+"23648/secret_warriors_2009_1",
 ("Fantastic Four","#570"): I+"25182/fantastic_four_1998_570",
 ("S.H.I.E.L.D. (2010)","#1"): I+"31599/shield_2010_1",
 ("FF","#1"): I+"37398/ff_2011_1",
 ("Avengers","#1"): I+"43528/avengers_2012_1",
 ("New Avengers","#1"): I+"43512/new_avengers_2013_1",
 ("Infinity","#1"): I+"47120/infinity_2013_1",
 ("Ultimate Comics: Thor","#1"): I+"33579/ultimate_thor_2010_1",
 ("Ultimate Comics: Fallout","#2"): I+"39966/ultimate_fallout_2011_2",
 ("Ultimate Comics: Hawkeye","#1"): I+"38950/ultimate_comics_hawkeye_2011_1",
 ("Ultimate Comics: Ultimates","#1"): I+"38693/ultimate_comics_ultimates_2011_1",
}
def L(*pairs): return [{"label":a,"url":b} for a,b in pairs]

# Links live on section headers, never on rows: a row's link only ever repeated
# the series link already sitting above it. AVID, SWID and FIRST are kept
# because they were confirmed by hand against Marvel's database and are tedious
# to rebuild, but nothing emits them any more.
def av(n, note="", star=0):
    return {"t": "Avengers", "n": "#%d" % n, "note": note, "star": star}
def na(n, note="", star=0):
    return {"t": "New Avengers", "n": "#%d" % n, "note": note, "star": star}
def sw(n, note="", star=0):
    return {"t": "Secret Wars", "n": "#%d" % n, "note": note, "star": star}
def it(t, n, note="", star=0, opt=0):
    return {"t": t, "n": n, "note": note, "star": star, "opt": opt}

F4N = {570:("\u201cSolve everything\u201d \u2014 the thesis statement for the whole saga",2),
       583:("\u201cPrime elements\u201d begins",1),
       587:("\u201cThree,\u201d part 4 \u2014 the most talked-about issue of the run",2),
       588:("The silent issue \u2014 no dialogue at all",1)}

SECTIONS = [
 {"id":"shield","tier":3,"title":"S.H.I.E.L.D.","sub":"2010\u20132011 \u00b7 come back to it later, but it rules","series":L(("Vol. 1",S_SH1),("Vol. 2",S_SH2)),
  "intro":'This one rules. It is dense, it is complicated, and it sits off to one side of everything else here \u2014 so leaving it until later costs you nothing, and picking it up cold is genuinely hard going.\n\nCome back for it though. It is one of the coolest comic series anyone has made.',
  "items":[it("S.H.I.E.L.D. (2010)","#%d"%n) for n in range(1,7)]
        + [it("S.H.I.E.L.D.: Infinity","#1")]
        + [it("S.H.I.E.L.D. (2011)","#%d"%n, "the back half was heavily delayed" if n==6 else "") for n in range(1,7)]},

 {"id":"warriors","tier":3,"title":"Secret Warriors","sub":"2009\u20132011 \u00b7 good comic, contributes almost nothing","series":L(("Secret Warriors",S_WAR)),"intro":'Nick Fury ran the world’s intelligence apparatus for decades. In the events just before this, he lost it — S.H.I.E.L.D. was dismantled after an alien infiltration was found to have reached the top of it, and what replaced it answered to someone worse.\n\nSo Fury goes underground and builds his own thing instead: off the books, staffed with young people whose powers nobody has on file.\n\nNone of that backstory is required. This is a spy comic that happens to share an author.',
  "items":[it("Secret Warriors","#%d"%n) for n in range(1,29)]},

 {"id":"darkreign","tier":2,"title":"Prelude \u2014 Dark Reign","sub":"start here \u00b7 where the Fantastic Four run begins","series":L(("Dark Reign: FF",S_DRF)),"start":1,"intro":'You don’t need to have read anything before this — but two things have just happened.\n\nA superhuman registration law tore the hero community in half, and Reed Richards was one of its architects. By any reasonable measure, he was wrong. It cost him friendships, and for a while it cost him his marriage.\n\nThen an alien infiltration of Earth ended with Norman Osborn shooting the invading queen on live television. He was rewarded with control of the country’s entire security apparatus — which he has spent the months since dismantling and rebuilding in his own image, with his own Avengers.\n\nSo: Osborn runs national security, and has opinions about who else should be allowed to. And Reed Richards is privately certain he made the worst call of his life. Rather than sit with that, he starts building a machine to ask every other version of himself how they would have handled it.\n\nSix years of story come out of that one decision.',
  # The Cabal one-shot came out before Dark Reign: FF #1 and is the earliest
  # thing Hickman wrote here, so it opens the section rather than trailing it
  "items":[it("Dark Reign: The Cabal","",'Hickman\u2019s story only \u2014 the earliest chapter here')]
        + [it("Dark Reign: Fantastic Four","#%d"%n) for n in range(1,6)]},

 {"id":"ff570","tier":2,"title":"Fantastic Four #570\u2013588","sub":"the run proper","series":L(("Fantastic Four",S_F4)),
  "items":[it("Fantastic Four","#%d"%n, F4N.get(n,("",0))[0], F4N.get(n,("",0))[1]) for n in range(570,589)]},

 {"id":"ff1","tier":2,"title":"FF #1\u201311","sub":"these are #589\u2013599 in legacy numbering \u2014 not a separate story","series":L(("FF",S_FF)),
  "items":[it("FF","#%d"%n, "the Future Foundation forms" if n==1 else "", 1 if n==1 else 0) for n in range(1,12)]},

 {"id":"weave","tier":2,"title":"The alternating weave","sub":"F4 #600\u2013611 \u00d7 FF #12\u201323 \u00b7 order specified by Hickman","series":L(("F4",S_F4),("FF",S_FF)),
  "items":[
   it("Fantastic Four","#600","oversized anniversary \u2014 read all the backups",1),
   it("FF","#12"), it("Fantastic Four","#601"), it("FF","#13"),
   it("Fantastic Four","#602"), it("FF","#14"), it("Fantastic Four","#603"),
   it("FF","#15","ends partway inside #604"),
   it("Fantastic Four","#604","the climax of the arc that began at #600",1),
   it("FF","#16","direct sequel to #604"),
   it("Fantastic Four","#605"),
   it("Fantastic Four","#605.1","alternate-universe side story",0,1),
   it("Fantastic Four","#606"), it("FF","#17"), it("FF","#18"),
   it("Fantastic Four","#607","Wakanda, part 1"),
   it("Fantastic Four","#608","Wakanda, part 2"),
   it("FF","#19"), it("FF","#20"),
   it("FF","#21","concurrent with the Wakanda two-parter"),
   it("Fantastic Four","#609"), it("Fantastic Four","#610"),
   it("FF","#22","retells part of #610 from another angle"),
   it("Fantastic Four","#611","the finale",2),
   it("FF","#23","Hickman\u2019s last word on this family",2)]},

 {"id":"ultopt","tier":3,"title":"Ultimate lead-in","sub":"Hickman, but disconnected \u2014 optional","series":L(("Thor",S_UTH),("Fallout",S_UFA),("Hawkeye",S_UHA)),"intro":'This is a different universe, and it’s supposed to feel that way.\n\nFrom 2000, Marvel ran a parallel line retelling its characters from scratch for new readers — same names, no continuity baggage, harder edges. By the time Hickman arrives, that world has been through a catastrophe that killed a large share of its heroes, and its Spider-Man has died and been replaced by a teenager most readers hadn’t met.\n\nThe one thing worth carrying forward: this world’s Reed Richards is not the man you’ve been reading about. He went somewhere very dark in books that aren’t listed here, and he now calls himself the Maker.\n\nRemember the name. It’s the part the main story eventually needs.',
  "items":[it("Ultimate Comics: Thor","#%d"%n) for n in range(1,5)]
        + [it("Ultimate Comics: Fallout","#%d"%n,"Hickman\u2019s chapters only") for n in range(2,7)]
        + [it("Ultimate Comics: Hawkeye","#%d"%n) for n in range(1,5)]},

 {"id":"ultimates","tier":1,"title":"Ultimate Comics: The Ultimates","sub":"establishes the Maker \u2014 pays off much later",
  "series":L(("Ultimates",S_UL)),"intro":'Same parallel universe as the previous section. If you skipped that one, the only thing to carry in is that this world’s Reed Richards turned villain some time ago and goes by the Maker now.',
  "items":[it("Ultimate Comics: Ultimates","#%d"%n) for n in range(1,13)]},

 {"id":"part1","tier":1,"title":"Avengers \u00d7 New Avengers, part one","sub":"two books, one story \u00b7 2012\u20132013",
  "series":L(("Avengers",S_AV),("New Avengers",S_NA)),"intro":'Two things happened just before this that aren’t in this list.\n\nThe Avengers and the X-Men fought a war over a returning cosmic force. It ended badly for everyone, with the X-Men’s founder dead and the hero community trusting itself less than it had in years. Hickman’s first issue opens in that aftermath — which is why the team is being rebuilt from scratch, and rebuilt enormous.\n\nThe second is older and quieter. Years ago a handful of the most powerful men in the Marvel Universe — Iron Man, Reed Richards, Namor, Black Bolt, Doctor Strange, Professor X — formed a private group to make the decisions nobody had elected them to make. They called themselves the Illuminati. It went badly enough that they stopped. New Avengers #1 is about them starting again.\n\nYou’ve seen these people be heroes. This is the book about what they do when no one is watching.',
  "items":[na(1,"\u201cEverything dies\u201d \u2014 the best opening issue of the saga",2), na(2), na(3),
   av(1,"\u201cWe need to get bigger\u201d",1), av(2), av(3), av(4), na(4), av(5),
   na(5), na(6,"where the book\u2019s central moral problem grows teeth",1)]
   + [av(n) for n in range(6,14)] + [na(7)]
   + [av(14,"prelude to Infinity begins",1), av(15), av(16), av(17), na(8)]},

 {"id":"infinity","tier":1,"title":"The Infinity weave","sub":"read strictly in this order \u2014 the cuts are deliberate","series":L(("Infinity",S_IN),("Avengers",S_AV),("New Avengers",S_NA)),
  "items":[it("Infinity","#1","",2), av(18), na(9),
   it("Infinity","#2"), av(19), na(10),
   it("Infinity","#3"), av(20),
   it("Infinity","#4"), av(21), na(11),
   it("Infinity","#5","",1), av(22), av(23),
   it("Infinity","#6","the event concludes",2)]},

 {"id":"incursions","tier":1,"title":"The Incursions","sub":"2014 \u00b7 the cosmic scale recedes and the rot takes over",
  "series":L(("Avengers",S_AV),("New Avengers",S_NA),("Avengers World",S_AWO)),
  "items":[na(12), av(24,"a.k.a. #24.NOW")]
   + [it("Avengers World","#%d"%n,"co-plotted by Hickman \u2014 optional",0,1) for n in range(1,15)]
   + [na(13), na(14), na(15)] + [av(n) for n in range(25,29)]
   + [na(16,"#16.NOW"), na(17)]
   + [av(29,"\u201cInfinite Avengers\u201d",1)] + [av(n) for n in range(30,35)]
   + [na(18,"a major new arc opens",1)] + [na(n) for n in range(19,24)]
   + [it("New Avengers Annual","#1","",0,1),
      it("Avengers","#34.1","",0,1), it("Avengers","#34.2","",0,1)]},

 {"id":"tro","tier":1,"title":"Time Runs Out","sub":"an eight-month jump \u00b7 the strongest sustained stretch",
  "series":L(("Avengers",S_AV),("New Avengers",S_NA)),"intro":'The story jumps forward eight months, and two people return changed for reasons that happened in other books.\n\nSteve Rogers is old. A villain drained the super-soldier serum out of him over in his own title, and he aged into the man he would have been had he never been frozen. Sam Wilson — the Falcon — carries the shield now.\n\nTony Stark is wrong. A magical event inverted the moral compass of a number of heroes and villains. Most were changed back. Tony preferred it, and arranged to stay that way.\n\nNeither is explained on the page, and neither is worth reading first. But if you hit these issues wondering whether you missed something: you didn’t.',
  "items":[av(35,"eight months later",1), na(24), na(25), av(36), av(37), na(26),
   av(38), na(27), av(39), na(28), av(40), na(29,"a pivotal issue",1),
   av(41), na(30), av(42), na(31), av(43), na(32),
   av(44,"",2), na(33,"the end of the run",2)]},

 {"id":"secretwars","tier":1,"title":"Secret Wars","sub":"2015 \u00b7 with Siege and Thors woven in",
  "series":L(("Secret Wars",S_SW),("Siege",S_SIE),("Thors",S_THO)),"intro":'Two miniseries run alongside the main book and are woven in below. They aren’t bonus material — they were published concurrently and are paced to sit between its issues.\n\nSiege is the one most guides call outright necessary: it covers the defence of Battleworld’s border, which the main series treats as already understood. Thors is a police procedural set in the same world — skippable in the strict sense, but it’s the best-executed tie-in of the event and it lands harder here than it would afterwards.\n\nThe remaining several dozen Secret Wars tie-ins are self-contained stories set in other corners of Battleworld. None of them are needed.',
  "items":[it("FCBD 2015: Secret Wars","#0","optional primer",0,1),
   sw(1,"",2), sw(2,"Battleworld",1), sw(3), sw(4),
   it("Secret Wars: Thors","#1","Battleworld police procedural",1,1),
   it("Secret Wars: Thors","#2","",0,1),
   it("Secret Wars: Thors","#3","",0,1),
   sw(5),
   it("Secret Wars: Siege","#1","the one tie-in most guides call necessary",1),
   it("Secret Wars: Siege","#2"),
   it("Secret Wars: Siege","#3"),
   sw(6),
   it("Secret Wars: Siege","#4"),
   it("Secret Wars: Thors","#4","",0,1),
   sw(7), sw(8),
   sw(9,"the payoff for everything above",2)]},

 {"id":"tieins","tier":3,"title":"Coda \u2014 Ultimate End","sub":"the Ultimate line\u2019s send-off \u00b7 optional","series":L(("Ultimate End",S_UEN)),
  "intro":"Bendis and Bagley, who launched the Ultimate line in 2000, were given the job of closing it. "
          "It is widely considered a disappointment, and it doesn\u2019t connect to Hickman\u2019s plot. "
          "Listed for completeness rather than recommended.",
  "items":[it("Ultimate End","#%d"%n,"",0,1) for n in range(1,6)]},
]


def fold(t):
    """The title half of a row id. Every run of anything but a-z and 0-9 is
    one dash, so a straight and a curly apostrophe fold alike; it is its own
    function so tools/idsafe.py can call it and prove that (CLU-652)."""
    base = t.lower()
    base = base.replace("&", "and")
    return re.sub(r"[^a-z0-9]+", "-", base).strip("-")


def slug(t, n):
    base = fold(t)
    num = n.lower().lstrip("#") or "0"
    num = re.sub(r"[^a-z0-9.]+", "-", num).strip("-")
    return base + "-" + num if num else base

def build_sections():
    """Finalise the reading order: assign stable slug ids, attach first-issue
    links, fill defaults. Raises if two items would collide on an id."""
    seen = {}
    for s in SECTIONS:
        for x in s["items"]:
            k = slug(x["t"], x["n"])
            if k in seen:
                raise ValueError("duplicate id %r (%s %s)" % (k, x["t"], x["n"]))
            seen[k] = 1
            x["id"] = k
            x.setdefault("note", "")
            x.setdefault("star", 0)
            x.setdefault("opt", 0)
    return SECTIONS


if __name__ == "__main__":
    secs = build_sections()
    n = sum(len(s["items"]) for s in secs)
    print("sections: %d   items: %d" % (len(secs), n))
    for s in secs:
        print("  T%d  %-34s %3d" % (s["tier"], s["title"], len(s["items"])))
