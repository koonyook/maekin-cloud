import MySQLdb

db = MySQLdb.connect('158.108.34.12', 'koon', '1q2w3e4r', 'middleware' )

cursor = db.cursor()

conditionString=''

#cursor.execute('''SELECT 
#`hostID`, `hostName`,`status`,`activity`,`MACAddress`,`IPAddress`,`isHost`,`isGlobalController`,`isInformationServer`,`isStorageHolder` 
#FROM `hosts`'''+conditionString+";")

#cursor.execute('''SELECT `MACAddress` FROM `hosts` UNION SELECT `MACAddress` FROM `guests`''')


cursor.execute('''
SELECT `guest_ip_pool`.`IPAddress` FROM 
				`guest_ip_pool` LEFT JOIN `guests` ON `guest_ip_pool`.`IPAddress`=`guests`.`IPAddress`
			WHERE `guests`.`IPAddress` IS NULL
			''')
print cursor.fetchall()
#print cursor.fetchone()
#print cursor.fetchone()
#print cursor.fetchone()
#print cursor.fetchone()
#for element in cursor:
#	print element

db.close()
