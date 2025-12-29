import pyodbc
def connect( statementSQL,queryType,params):
        try:
            cs = (
                r"Driver={SQL Server};"
                r"Server=THE_MACHINE\SQLEXPRESS;"
                r"Database=Database;"
                r"Trusted_Connection=yes;"
            )
            
            cnx = pyodbc.connect(cs)
            print("Connected")
            if cnx is not None:
                cursor = cnx.cursor()
                if params is not None:
                    cursor.execute(statementSQL,params)
                else:
                    cursor.execute(statementSQL) 
                if queryType == "one":
                    row=cursor.fetchone()
                    return row
                if queryType == "many":
                    rows=cursor.fetchall()
                    return rows
                if queryType == "none":
                    cnx.commit()
                    print("Commited")
                    return None
        except pyodbc.DatabaseError as err:
            print(err)
        finally:
            if 'cnx' in locals() and cnx:
                cnx.close()
            print("Connection Closed")
print(connect(statementSQL="SELECT Name,WeightClass,Birthdate,Gym  FROM Fighters",queryType="many",params=None))
