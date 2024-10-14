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

Here are some basic SQLite queries. Since the database also supports full text search (FTS), these
can sometimes be more difficult to write or produce unintuitive results. 

```sql
-- Name and title are not always the same.
select name, title from mycota where name <> title;

-- Non-FTS queries that use `like` are case-sensitive by default. Only title and name have capital letters.
-- Non-FTS `like` is the only way to do substring search.
select title, name, whichGills from mycota where lower(name) like '%tricholoma%';

-- Search where whichGills is _only_ 'free' and no other values.
-- The output is wide, so this will occlude some columns based on your terminal width.
select * from mycota where whichGills = 'free';

-- hymeniumType is a non-aggregate field so these semantics are simple.
select title, sporePrintColor from mycota where hymeniumType = 'gleba';

-- group by an aggregate field, so show _all_ combinations of ecologicalType where there is at least one stipeCharacter
select count(1), ecologicalType from mycota where stipeCharacter is not null group by ecologicalType;

-- query on two simple fields and show the coalesce necessary to account for nulls.
-- Using an equivalent FTS form is easier than this.
select title, eat from (
    select title, coalesce(howEdible1, '') || ' ' || coalesce(howEdible2, '') as eat
    from mycota
) where eat like '%choice%';

-- another rough equivalent to above
select title, howEdible1, howEdible2 from mycota where howEdible1='choice' or howEdible2='choice';

-- Feeling lucky? Edibility defined but whichGills and capShape undefined.
select title, howEdible1, howEdible2 from mycota 
where howEdible1 is not null and howEdible2 is not null and whichGills is null and capShape is null;
```

Full text search queries are also possible using the syntax from the
[fts5 module](https://sqlite.org/fts5.html#full_text_query_syntax).

Briefly,

- it's a query sub-language that must be written in string literals;
- all query keywords are case-sensitive CAPITALS;
- all column data are case-insensitive;
- it does not perform sub-token searches, only token searches; and
- you can search over multiple (even all) columns by writing the table name (`mycota`) before `match`.

```sql
-- howEdible contains at least one of each token in this phrase
select title, howEdible from mycota where howEdible match 'choice deadly';

-- title contains token 'esculenta'
select title, howEdible from mycota where mycota match 'esculenta';

-- search for either of two genera from either name or title
select title, ecologicalType from mycota where mycota match '({name title}: amanita) OR ({name title}: leucocoprinus)'
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
5            edible       298
6          inedible       204
7   not recommended         5
8         poisonous        91
9      psychoactive        69
10  too hard to eat         2
11          unknown       410
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
```
