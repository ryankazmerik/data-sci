SELECT count(*), lkupclientid, MAX(scoredate) as scoredate
FROM stlrflames.dw.customerretentionscores
GROUP BY lkupclientid
ORDER BY scoredate DESC



CALL dw.getretentionmodeldata(11, 2010, 2021, 'temp_cursor');
FETCH ALL FROM temp_cursor;

CALL ds.getretentionmodeldata(31, 2021, 2022, 'temp_cursor');
FETCH ALL FROM temp_cursor;


select * 
from dw.customerretentionscores c 
where lkupclientid = 31
and scoredate = '2022-06-22'

select count(distinct dimcustomermasterid)
from dw.cohortretentionscore c 
where date_effective_end  is null
and lkupclientid  = 31
and seasonyear = 2022
and score between 0 and 5
;