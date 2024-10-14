Setting up
----------

Install at least Python 3.12 on your operating system. Optionally set up a virtual environment. Then,

```shell
pip install -r requirements.txt
```


Running
-------

```shell
python -m mycota -h
```


Example queries
---------------

Basic SQLite queries:

```sql
select title, name, whichGills from mycota where lower(name) like '%tricholoma%';

-- Will occlude some columns based on your terminal width
 select * from mycota where whichGills = 'free';

select title, sporePrintColor1, sporePrintColor2 from mycota where hymeniumType = 'gleba';

select count(1), ecologicalType from mycota where stipeCharacter is not null group by ecologicalType;

select title, eat from (
    select title, lower(coalesce(howEdible1, '') || ' ' || coalesce(howEdible2, '')) as eat
    from mycota
) where eat like '%choice%';

-- Feeling lucky?
select title, howEdible1, howEdible2 from mycota 
where howEdible1 is not null and howEdible2 is not null and whichGills is null and capShape is null;
```

Full text search queries are also possible using the syntax from the
[fts5 module](https://sqlite.org/fts5.html#full_text_query_syntax).

Briefly,

- it's a query sub-language that exists in string literals;
- all query keywords are case-sensitive CAPITALS;
- all data are case-insensitive;
- it does not perform sub-token searches, only token searches; and
- you can search over multiple (even all) columns by writing the table name before `match`.

```sql
select title, howEdible from mycota where howEdible match 'NEAR(choice deadly)';

select title, howEdible from mycota where mycota match 'esculenta';

select title, howEdible from mycota where mycota match '({name title}: amanita) AND ({howEdible}: edible)' 
```

Schema
------

As of this writing, the output of `-s` is

```sql
CREATE VIRTUAL TABLE mycota using fts5(pageid, capShape1, capShape2, ecologicalType1, ecologicalType2, howEdible1, howEdible2, hymeniumType, name, sporePrintColor1, sporePrintColor2, stipeCharacter1, stipeCharacter2, title, whichGills1, whichGills2, whichGills3, capShape, ecologicalType, howEdible, sporePrintColor, stipeCharacter, whichGills)
```

and the output of `-c` (somewhat covering the same feature as [the Template Parameters Bot](https://bambots.brucemyers.com/TemplateParam.php?wiki=enwiki&template=Mycomorphbox)) is

```none
          capShape1  count(*)
0              None       240
1       campanulate        66
2           conical       139
3            convex       857
4         depressed        54
5              flat        78
6   infundibuliform        51
7         irregular         3
8            offset        29
9             ovate        24
10       umbilicate         3
11         umbonate        34
12          unknown         1

          capShape2  count(*)
0              None      1066
1          aplanate         1
2       campanulate        38
3           conical        24
4            convex        77
5         depressed        70
6              flat       217
7   infundibuliform         8
8            offset         7
9             ovate         9
10       umbilicate         3
11         umbonate        59

  ecologicalType1  count(*)
0            None        89
1      ascomycete         1
2     mycorrhizal       531
3       parasitic        48
4    saprotrophic       910

  ecologicalType2  count(*)
0            None      1529
1     mycorrhizal        13
2       parasitic        29
3    saprotrophic         8

         howEdible1  count(*)
0              None       264
1        allergenic         2
2           caution        58
3            choice       131
4            deadly        30
5            edible       297
6          inedible       204
7   not recommended         5
8         poisonous        91
9      psychoactive        69
10  too hard to eat         2
11          unknown       411
12      unpalatable        15

         howEdible2  count(*)
0              None      1415
1        allergenic         9
2           caution        48
3            choice         8
4            deadly         7
5            edible         8
6          inedible        33
7   not recommended         4
8         poisonous        20
9      psychoactive        13
10  too hard to eat         1
11          unknown         9
12      unpalatable         4

  hymeniumType  count(*)
0         None        19
1        gills      1078
2        gleba       103
3        pores       198
4       ridges        36
5       smooth       120
6        teeth        24
7      unknown         1

   sporePrintColor1  count(*)
0              None       395
1             black        38
2    blackish-brown        30
3             brown       187
4              buff        13
5             cream        41
6             green         2
7             ochre        14
8             olive        23
9       olive-brown        73
10             pink        32
11    pinkish-brown         4
12           purple         4
13     purple-black         5
14     purple-brown        50
15    reddish-brown        28
16           salmon         5
17              tan         9
18            white       557
19           yellow        47
20     yellow-brown         7
21    yellow-orange        15

   sporePrintColor2  count(*)
0              None      1431
1             black         2
2    blackish-brown         3
3             brown        17
4              buff        11
5             cream        27
6             ochre         1
7             olive         3
8       olive-brown         6
9            orchre         3
10             pink         6
11    pinkish-brown         6
12           purple         7
13     purple-black         2
14     purple-brown         4
15    reddish-brown         7
16           salmon         6
17            white         7
18           yellow        27
19     yellow-brown         2
20    yellow-orange         1

  stipeCharacter1  count(*)
0            None       456
1            bare       765
2         cortina        25
3            ring       214
4  ring and volva        66
5         unknown         3
6           volva        50

  stipeCharacter2  count(*)
0            None      1558
1            bare         8
2         cortina         3
3            ring        10

    whichGills1  count(*)
0          None       361
1        adnate       365
2       adnexed       351
3     decurrent       180
4    emarginate        12
5          free       295
6      seceding         5
7       sinuate         3
8  subdecurrent         6
9       unknown         1

     whichGills2  count(*)
0           None      1178
1         adnate       245
2        adnexed        44
3      decurrent        46
4     emarginate         3
5           free        19
6        notched         2
7       seceding         5
8        sinuate        27
9   subdecurrent         9
10          waxy         1

  whichGills3  count(*)
0        None      1578
1        free         1

                      capShape  count(*)
0                         None       238
1                  campanulate        12
2         campanulate, conical         9
3          campanulate, convex        21
4       campanulate, depressed         1
5            campanulate, flat        15
6           campanulate, ovate         2
7        campanulate, umbonate         6
8                      conical        68
9         conical, campanulate        20
10             conical, convex        22
11               conical, flat         9
12              conical, ovate         7
13           conical, umbonate        13
14                      convex       562
15            convex, aplanate         1
16         convex, campanulate        10
17             convex, conical        12
18           convex, depressed        54
19                convex, flat       178
20     convex, infundibuliform         4
21              convex, offset         1
22          convex, umbilicate         2
23            convex, umbonate        33
24                   depressed        42
25           depressed, convex         4
26  depressed, infundibuliform         3
27           depressed, offset         3
28       depressed, umbilicate         1
29         depressed, umbonate         1
30                        flat        35
31               flat, conical         1
32                flat, convex        24
33             flat, depressed        13
34       flat, infundibuliform         1
35                flat, offset         1
36              flat, umbonate         3
37             infundibuliform        50
38       infundibuliform, flat         1
39                   irregular         3
40                      offset        29
41              offset, convex         1
42           offset, depressed         1
43                       ovate         3
44          ovate, campanulate         6
45              ovate, conical         1
46               ovate, convex         2
47                 ovate, flat         9
48             ovate, umbonate         3
49                  umbilicate         3
50                    umbonate        22
51       umbonate, campanulate         2
52           umbonate, conical         1
53            umbonate, convex         3
54         umbonate, depressed         1
55              umbonate, flat         5
56                     unknown         1

              ecologicalType  count(*)
0                       None        88
1                 ascomycete         1
2                mycorrhizal       528
3     mycorrhizal, parasitic         1
4  mycorrhizal, saprotrophic         3
5                  parasitic        43
6    parasitic, saprotrophic         5
7               saprotrophic       870
8  saprotrophic, mycorrhizal        12
9    saprotrophic, parasitic        28

                     howEdible  count(*)
0                         None       264
1                   allergenic         2
2                      caution        50
3              caution, deadly         1
4              caution, edible         2
5            caution, inedible         1
6           caution, poisonous         1
7             caution, unknown         3
8                       choice       109
9           choice, allergenic         4
10             choice, caution        10
11              choice, edible         3
12            choice, inedible         4
13           choice, poisonous         1
14                      deadly        28
15              deadly, choice         2
16                      edible       221
17          edible, allergenic         4
18             edible, caution        38
19              edible, choice         5
20            edible, inedible        17
21     edible, not recommended         2
22           edible, poisonous         3
23        edible, psychoactive         1
24     edible, too hard to eat         1
25             edible, unknown         3
26         edible, unpalatable         2
27                    inedible       192
28            inedible, edible         2
29         inedible, poisonous         5
30      inedible, psychoactive         1
31           inedible, unknown         2
32       inedible, unpalatable         2
33             not recommended         4
34  not recommended, poisonous         1
35                   poisonous        74
36       poisonous, allergenic         1
37           poisonous, deadly         5
38     poisonous, psychoactive        11
39                psychoactive        68
40        psychoactive, edible         1
41             too hard to eat         2
42                     unknown       387
43             unknown, choice         1
44             unknown, deadly         1
45           unknown, inedible        11
46    unknown, not recommended         2
47          unknown, poisonous         9
48                 unpalatable        14
49        unpalatable, unknown         1

                 sporePrintColor  count(*)
0                           None       395
1                          black        35
2          black, blackish-brown         1
3                   black, brown         1
4                   black, white         1
5                 blackish-brown        18
6          blackish-brown, black         2
7          blackish-brown, brown         5
8         blackish-brown, purple         5
9                          brown       174
10         brown, blackish-brown         2
11                  brown, ochre         1
12            brown, olive-brown         1
13                 brown, purple         2
14           brown, purple-brown         1
15          brown, reddish-brown         3
16                 brown, yellow         1
17           brown, yellow-brown         2
18                          buff         8
19                   buff, cream         1
20                    buff, pink         3
21           buff, reddish-brown         1
22                         cream        22
23                   cream, buff         2
24                 cream, salmon         4
25                  cream, white         3
26                 cream, yellow        10
27                         green         2
28                         ochre        12
29                  ochre, brown         1
30                   ochre, buff         1
31                         olive        18
32                  olive, brown         3
33            olive, olive-brown         2
34                   olive-brown        73
35                          pink        21
36                   pink, brown         1
37                   pink, cream         1
38           pink, pinkish-brown         6
39                  pink, salmon         2
40                   pink, white         1
41                 pinkish-brown         3
42  pinkish-brown, reddish-brown         1
43                        purple         2
44                 purple, brown         1
45          purple, purple-brown         1
46                  purple-black         4
47           purple-black, olive         1
48                  purple-brown        49
49    purple-brown, purple-black         1
50                 reddish-brown        27
51   reddish-brown, purple-brown         1
52                        salmon         4
53         salmon, reddish-brown         1
54                           tan         6
55                    tan, brown         1
56            tan, reddish-brown         1
57                   tan, yellow         1
58                         white       504
59                  white, brown         1
60                   white, buff         4
61                  white, cream        24
62                  white, olive         1
63            white, olive-brown         2
64                   white, pink         3
65           white, purple-black         1
66           white, purple-brown         1
67                 white, yellow        15
68          white, yellow-orange         1
69                        yellow        34
70                 yellow, brown         2
71                  yellow, buff         4
72                 yellow, cream         1
73                 yellow, olive         1
74                yellow, orchre         3
75                 yellow, white         2
76                  yellow-brown         6
77     yellow-brown, olive-brown         1
78                 yellow-orange        14
79          yellow-orange, brown         1

   stipeCharacter  count(*)
0            None       453
1            bare       755
2   bare, cortina         3
3      bare, ring        10
4         cortina        25
5            ring       209
6  ring and volva        66
7      ring, bare         5
8         unknown         3
9           volva        50

                 whichGills  count(*)
0                      None       360
1                    adnate       241
2           adnate, adnexed        35
3         adnate, decurrent        46
4        adnate, emarginate         2
5              adnate, free         8
6          adnate, seceding         5
7           adnate, sinuate        23
8      adnate, subdecurrent         6
9                   adnexed       101
10          adnexed, adnate       234
11            adnexed, free        11
12         adnexed, notched         2
13         adnexed, sinuate         2
14   adnexed, sinuate, free         1
15                decurrent       174
16        decurrent, adnate         4
17  decurrent, subdecurrent         2
18               emarginate        10
19       emarginate, adnate         1
20         emarginate, waxy         1
21                     free       280
22             free, adnate         4
23            free, adnexed         9
24         free, emarginate         1
25            free, sinuate         1
26                 seceding         5
27                  sinuate         2
28    sinuate, subdecurrent         1
29             subdecurrent         5
30     subdecurrent, adnate         1
31                  unknown         1
```
