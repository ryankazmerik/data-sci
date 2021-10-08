import pandas as pd
import pyodbc

SERVER = '52.44.171.130' 
DATABASE = 'datascience' 
USERNAME = 'nrad' 
PASSWORD = 'ThisIsQA123' 
CNXN = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER='+SERVER+';DATABASE='+DATABASE+';UID='+USERNAME+';PWD='+ PASSWORD)


data = {'dimcustomermasterid': ['1', '2', '2', '4'],
 'buyer_score': [0.00, 0.00, 0.00, 0.00],
  'year': [1,1,1,1],
  'lkupclientid': [1,1,1,1],
  'productgrouping': ['test','test','test','test'],
  'insertDate': ['09-01-2021 13:47:49','09-01-2021 13:47:49','09-01-2021 13:47:49','09-01-2021 13:47:49']
  }

df_scores = pd.DataFrame(data)

def write_scores_to_sql():

    cursor = CNXN.cursor()
    for index, row in df_scores.iterrows(): # the table needs to change to finalscore
        cursor.execute("INSERT INTO ds.newfinalscore (dimcustomermasterid,buyer_score,year,lkupclientid,productgrouping,insertDate) values(" + str(row.dimcustomermasterid) + "," + str(round(row.buyer_score,4))+ ","+ str(row.year) + "," + str(row.lkupclientid)+ ","+"'"+str(row.productgrouping)+"'"+ "," +"'"+str(row.insertDate)+"'" + ")")
    CNXN.commit()
    cursor.close()

if __name__ == "__main__":
    write_scores_to_sql()