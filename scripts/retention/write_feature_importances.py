import pandas as pd
import pyodbc
SERVER = '52.44.171.130' 
DATABASE = 'datascience' 
USERNAME = 'nrad' 
PASSWORD = 'ThisIsQA123' 
CNXN = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+SERVER+';DATABASE='+DATABASE+';UID='+USERNAME+';PWD='+ PASSWORD)


data = {'attribute': ['test1', 'test2', 'test3'],
 'product': ['test','test','test'],
  'indexValue': [1,1,1],
  'rank': [1,1,1],
  'lkupClientId': [1,1,1],
  'modelVersnNumber': [0,0,0],
  'scoreDate': ['09-01-2021 13:47:49','09-01-2021 13:47:49','09-01-2021 13:47:49'],
  'loadId':[0,0,0]
  }

df_feature_importances = pd.DataFrame(data)

def write_feature_importances_to_sql():

    cursor = CNXN.cursor()
    for index, row in df_feature_importances.iterrows(): 
        cursor.execute("INSERT INTO stlrMILB.dw.lkupRetentionAttributeImportance (attribute,product,indexValue,rank,lkupClientId,modelVersnNumber,scoreDate,loadId) values(" + "'" +str(row.attribute)+"'"+","+ "'"+str(product_grouping)+"'" +"," + str(round(row.indexValue,4)) + "," + str(row.attrank)+ ","+ str(row.lkupClientId) + "," + str(row.modelVersnNumber)+ "," + "'"+ str(row.scoreDate)+ "'"+ ","+ str(row.loadId)  + ")")
    CNXN.commit()
    cursor.close()

if __name__ == "__main__":
    write_feature_importances_to_sql()