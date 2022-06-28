
CALL stlrtrailblazers.dw.geteventpropensityscoring(53, cast('2022-05-23' as date));
UNLOAD (
  'SELECT * from result_set;'
  )
TO 's3://stellaralgo-temp-redshift/eventpropensity/05-23/'
IAM_ROLE 'arn:aws:iam::173696899631:role/datascience-redshift-etl'
FORMAT PARQUET




CALL stlrmls.dw.geteventpropensityscoring(53, cast('2022-05-23' as date));
SELECT * from result_set;

CALL stlryankees.ds.geteventpropensitymodelinference(53, cast('2022-05-23' as date), 'temp_cursor');
FETCH ALL FROM temp_cursor;

CALL ds.geteventpropensitytrainingdata(35, 2022, 2023, 'rkcursor');
FETCH ALL FROM rkcursor;