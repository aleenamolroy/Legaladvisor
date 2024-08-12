import pymysql
from django.contrib.auth.hashers import make_password

conn = pymysql.connect(host='localhost', user='root', password='your_password', database='your_database')
cursor = conn.cursor()

cursor.execute("SELECT u_id, password FROM tbl_user")
users = cursor.fetchall()

for user_id, password in users:
    hashed_password = make_password(password)
    cursor.execute("UPDATE tbl_user SET password = %s WHERE u_id = %s", [hashed_password, user_id])

conn.commit()
cursor.close()
conn.close()
