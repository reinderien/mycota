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
CREATE TABLE "mycota" (
"pageid" INTEGER,
  "title" TEXT,
  "name" TEXT,
  "whichGills" TEXT,
  "capShape" TEXT,
  "hymeniumType" TEXT,
  "stipeCharacter" TEXT,
  "ecologicalType" TEXT,
  "sporePrintColor" TEXT,
  "howEdible" TEXT,
  "howEdible2" TEXT,
  "whichGills2" TEXT,
  "capShape2" TEXT,
  "sporePrintColor2" TEXT,
  "ecologicalType2" TEXT,
  "stipeCharacter2" TEXT,
  "whichGills3" TEXT
)
```

and the output of `-c` (somewhat covering the same feature as [the Template Parameters Bot](https://bambots.brucemyers.com/TemplateParam.php?wiki=enwiki&template=Mycomorphbox)) is

```none
     whichGills  count(*)
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

           capShape  count(*)
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

  hymeniumType  count(*)
0         None        19
1        gills      1078
2        gleba       103
3        pores       198
4       ridges        36
5       smooth       120
6        teeth        24
7      unknown         1

   stipeCharacter  count(*)
0            None       456
1            bare       765
2         cortina        25
3            ring       214
4  ring and volva        66
5         unknown         3
6           volva        50

  ecologicalType  count(*)
0           None        89
1     ascomycete         1
2    mycorrhizal       531
3      parasitic        48
4   saprotrophic       910

   sporePrintColor  count(*)
0             None       395
1            black        38
2   blackish-brown        30
3            brown       187
4             buff        13
5            cream        41
6            green         2
7            ochre        14
8            olive        23
9      olive-brown        73
10            pink        32
11   pinkish-brown         4
12          purple         4
13    purple-black         5
14    purple-brown        50
15   reddish-brown        28
16          salmon         5
17             tan         9
18           white       557
19          yellow        47
20    yellow-brown         7
21   yellow-orange        15

          howEdible  count(*)
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
0                      None      1415
1                allergenic         9
2                   caution        48
3   caution/not recommended         1
4                    choice         8
5                    deadly         7
6                    edible         8
7                  inedible        33
8           not recommended         3
9                 poisonous        20
10             psychoactive        13
11          too hard to eat         1
12                  unknown         9
13              unpalatable         4

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

  ecologicalType2  count(*)
0            None      1529
1     mycorrhizal        13
2       parasitic        29
3    saprotrophic         8

  stipeCharacter2  count(*)
0            None      1558
1            bare         8
2         cortina         3
3            ring        10

  whichGills3  count(*)
0        None      1578
1        free         1
```
