SELECT * FROM datascience.ds.datadictionary

INSERT INTO datascience.ds.datadictionary (
  feature, featureraw, datatype, source, engineered, description
)
VALUES ('Gender Not Available','gender_not_available','object','Pycaret',True,'The availability of the gender of the fan.')




CREATE OR REPLACE PROCEDURE ds.getRetentionDataset (
  param IN integer, 
  rs_out INOUT refcursor
) AS $$

BEGIN
  OPEN rs_out FOR SELECT * FROM ds.dummytable where playerid = param;
END;

$$ LANGUAGE plpgsql;



BEGIN;
CALL ds.getRetentionDataset(11, 'mycursor');

FETCH ALL FROM mycursor;
COMMIT;


BEGIN;
CALL dw.getretentionscoringmodeldata(11, 2021, 2022, 'rkcursor');

FETCH ALL FROM rkcursor;
COMMIT;