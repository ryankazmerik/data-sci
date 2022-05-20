CALL stlrmls.dw.getpropensityproductmulticlasstraining(6, 2021, 2022); 
SELECT * from result_set;

CALL stlrmls.dw.getpropensityproductmulticlassscoring(6, 2021, 2022);
select * from result_set_scoring;




CALL stlrmls.dw.getpropensityproductmulticlasstraining(6, 2021, 2022);
UNLOAD (
  'SELECT * from result_set;'
  )
TO 's3://stellaralgo-temp-redshift/productpropensity/'
IAM_ROLE 'arn:aws:iam::173696899631:role/datascience-redshift-etl'
FORMAT PARQUET


CALL stlrmls.dw.getpropensityproductmulticlassscoring(6, 2021, 2022);
UNLOAD (
  'SELECT * from result_set;'
  )
TO 's3://stellaralgo-temp-redshift/productpropensity/'
IAM_ROLE 'arn:aws:iam::173696899631:role/datascience-redshift-etl'
FORMAT PARQUET


CALL dw.getproductpropensitymodeldata(11, 2010, 2021, 'rkcursor');
FETCH ALL FROM rkcursor;
