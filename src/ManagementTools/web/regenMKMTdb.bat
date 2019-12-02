REM del mysqlite
REM python manage.py syncdb < command.txt
python manage.py reset mkmt < deluser1.txt
python manage.py shell < deluser2.txt
