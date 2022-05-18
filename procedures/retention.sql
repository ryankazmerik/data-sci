SELECT count(*), lkupclientid, MAX(scoredate) as scoredate
FROM stlrflames.dw.customerretentionscores
GROUP BY lkupclientid
ORDER BY scoredate DESC

SELECT * 
FROM stlrflames.dw.customerretentionscores


BEGIN;
CALL dw.getretentionmodeldata(11, 2010, 2021, 'rkcursor');
FETCH ALL FROM rkcursor;
COMMIT;
