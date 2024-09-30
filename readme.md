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

```sqlite-sql
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
