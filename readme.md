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

```sql
select title, name, whichGills from mycota where lower(name) like '%tricholoma%';

-- Will occlude some columns based on your terminal width
 select * from mycota where whichGills = 'free';

select title, sporePrintColor, sporePrintColor2 from mycota where hymeniumType = 'gleba';

select count(1), ecologicalType from mycota where stipeCharacter is not null group by ecologicalType;

select title, eat from (
    select title, lower(coalesce(howEdible, '') || ' ' || coalesce(howEdible2, '')) as eat
    from mycota
) where eat like '%choice%';

-- Feeling lucky?
select title, howEdible, howEdible2 from mycota 
where howEdible is not null and howEdible2 is not null and whichGills is null and capShape is null;
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
  "whichGills3" TEXT,
  "color" TEXT
)
```

and the output of `-c` is

```none
      whichGills  count(*)
0           None       360
1         adnate       365
2        adnexed       351
3      decurrent       180
4     emarginate        12
5           free       295
6          pores         1
7       seceding         5
8        sinuate         3
9   subdecurrent         6
10       unknown         1

           capShape  count(*)
0              None       240
1       campanulate        66
2           conical       139
3            convex       856
4         depressed        54
5              flat        78
6   infundibuliform        51
7         irregular         3
8            offset        29
9             ovate        23
10            ovoid         1
11     plano-convex         1
12       umbilicate         3
13         umbonate        34
14          unknown         1

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
1          NAbare         1
2            bare       764
3         cortina        25
4            ring       214
5  ring and volva        66
6         unknown         3
7           volva        50

  ecologicalType  count(*)
0           None        88
1   Saprotrophic         1
2     ascomycete         1
3    mycorrhizal       531
4      parasitic        48
5    saprotophic         1
6   saprotrophic       907
7    satrophytic         1
8        unknown         1

   sporePrintColor  count(*)
0             None       392
1            black        38
2   blackish-brown        30
3            brown       187
4             buff        13
5        colorless         1
6            cream        41
7            green         2
8            ochre        14
9            olive        23
10     olive-brown        73
11            pink        32
12   pinkish-brown         4
13          purple         4
14    purple-black         5
15    purple-brown        50
16   reddish-brown        28
17          salmon         5
18             tan         9
19         unknown         2
20           white       557
21          yellow        47
22    yellow-brown         7
23   yellow-orange        15

          howEdible  count(*)
0              None       263
1        allergenic         2
2           caution        59
3            choice       131
4            deadly        30
5            edible       296
6          inedible       204
7         non toxic         1
8   not recommended         5
9         poisonous        89
10     psychoactive        69
11  too hard to eat         2
12            toxic         1
13          unknown       411
14      unpalatable        15
15              yes         1

                                        howEdible2  count(*)
0                                             None      1415
1                                       allergenic         9
2                                          caution        48
3                          caution/not recommended         1
4                                           choice         8
5                                           deadly         7
6                                           edible         8
7                                         inedible        33
8                                  not recommended         3
9                                        poisonous        20
10  poisonous or potential psychoactive properties         1
11                                    psychoactive        12
12                                 too hard to eat         1
13                                         unknown         9
14                                     unpalatable         4

     whichGills2  count(*)
0           None      1177
1         adnate       245
2        adnexed        43
3        annexed         1
4      decurrent        46
5     emarginate         3
6           free        19
7        notched         2
8          pores         1
9       seceding         5
10       sinuate        27
11  subdecurrent         9
12          waxy         1

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

     color  count(*)
0     None      1578
1  #91FAFA         1
```
