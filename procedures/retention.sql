SELECT count(*), lkupclientid, MAX(scoredate) as scoredate
FROM stlrflames.dw.customerretentionscores
GROUP BY lkupclientid
ORDER BY scoredate DESC



CALL dw.getretentionmodeldata(11, 2010, 2021, 'temp_cursor');
FETCH ALL FROM temp_cursor;

CALL dw.getretentionmodeldata(6, 2020, 2022, 'temp_cursor');
FETCH ALL FROM temp_cursor;