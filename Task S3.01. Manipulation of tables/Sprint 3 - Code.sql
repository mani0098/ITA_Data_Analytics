# Sprint 2
########## Nivell 1
################### Exercici 1
# La teva tasca és dissenyar i crear una taula anomenada "credit_card" que emmagatzemi detalls crucials sobre les 
# targetes de crèdit. La nova taula ha de ser capaç d'identificar de manera única cada targeta i establir una 
# relació adequada amb les altres dues taules ("transaction" i "company"). Després de crear la taula serà necessari 
# que ingressis la informació del document denominat "dades_introduir_credit". Recorda mostrar el diagrama i 
# realitzar una breu descripció d'aquest.

USE transactions;

DROP TABLE IF EXISTS credit_card;
CREATE TABLE credit_card (
						  id 			VARCHAR(20) NOT NULL PRIMARY KEY,
						  iban 			VARCHAR(40) NOT NULL,
						  pan 			CHAR(20)    NOT NULL,
						  pin 			CHAR(5)		NOT NULL,
						  cvv 			CHAR(5)		NOT NULL,
						  expiring_date VARCHAR(10) NOT NULL
						  );

DESCRIBE credit_card;

SELECT COUNT(*)
FROM credit_card;

UPDATE credit_card
SET expiring_date = str_to_date(expiring_date, '%m/%d/%y')
WHERE id != '';

ALTER TABLE credit_card
MODIFY expiring_date DATE;

ALTER TABLE transaction
ADD CONSTRAINT card_transaction
FOREIGN KEY (credit_card_id)
REFERENCES credit_card(id);

################### Exercici 2
# El departament de Recursos Humans ha identificat un error en el número de compte associat a la targeta de 
# crèdit amb ID CcU-2938. La informació que ha de mostrar-se per a aquest registre és: TR323456312213576817699999. 
# Recorda mostrar que el canvi es va realitzar.

UPDATE credit_card 
SET iban = 'TR323456312213576817699999'
WHERE id = 'CcU-2938';

SELECT id, iban
FROM credit_card
WHERE id = 'CcU-2938';

################### Exercici 3
# En la taula "transaction" ingressa una nova transacció amb la següent informació:
# Id	            108B1D1D-5B23-A76C-55EF-C568E49A99DD
# credit_card_id	CcU-9999
# company_id	    b-9999
# user_id	        9999
# lat	            829.999
# longitude	        -117.999
# amount	        111.11
# declined	        0

INSERT INTO credit_card (id, iban, pan, pin, cvv, expiring_date) 
VALUES ('CcU-9999', 'TR323456312213576817699999', '6666777788889999', '6789', '899', '2029-09-29');
INSERT INTO company (id) 
VALUES ('b-9999');
INSERT INTO transaction (id, credit_card_id, company_id, user_id, lat, longitude, amount, declined) 
VALUES ('108B1D1D-5B23-A76C-55EF-C568E49A99DD', 'CcU-9999', 'b-9999', 9999, 829.999, -117.999, 111.11, 0);

################### Exercici 4
# Des de recursos humans et sol·liciten eliminar la columna "pan" de la taula credit_card. Recorda 
# mostrar el canvi realitzat.

ALTER TABLE credit_card
DROP COLUMN pan; 

SELECT *
FROM credit_card;

########## Nivell 2
################### Exercici 1
# Elimina de la taula transaction el registre amb ID 000447FE-B650-4DCF-85DE-C7ED0EE1CAAD de la base de 
# dades.

DELETE FROM transaction 
WHERE transaction.id = '000447FE-B650-4DCF-85DE-C7ED0EE1CAAD';

################### Exercici 2
# La secció de màrqueting desitja tenir accés a informació específica per a realitzar anàlisi i 
# estratègies efectives. S'ha sol·licitat crear una vista que proporcioni detalls clau sobre les 
# companyies i les seves transaccions. Serà necessària que creïs una vista anomenada VistaMarketing que 
# contingui la següent informació: Nom de la companyia, Telèfon de contacte, País de residència i Mitjana 
# de compra realitzat per cada companyia. Presenta la vista creada, ordenant les dades de major a menor 
# mitjana de compra.

CREATE VIEW VistaMarketing     AS
SELECT c.company_name 		   AS Company_Name, 
       c.phone		  		   AS Phone_Number, 
       c.country	  		   AS Country, 
       ROUND(AVG(t.amount),3)  AS Average
FROM company c
JOIN transaction t ON c.id = t.company_id
WHERE t.declined = 0
GROUP BY c.id, c.company_name, c.phone, c.country
ORDER BY Average DESC;

SELECT *
FROM VistaMarketing;

################### Exercici 3
# Filtra la vista VistaMarketing per a mostrar només les companyies que tenen el seu país de residència 
# en "Germany"

SELECT *
FROM VistaMarketing
WHERE Country = 'Germany';

########## Nivell 3
################### Exercici 1
# La setmana vinent tindràs una nova reunió amb els gerents de màrqueting. Un company del teu equip va 
# realitzar modificacions en la base de dades, però no recorda com les va realitzar. Et demana que 
# l'ajudis a deixar els comandos executats per a obtenir el següent diagrama:

# a la taula "user"
RENAME TABLE user TO data_user;    
ALTER TABLE data_user
MODIFY COLUMN id INT,
RENAME COLUMN email TO personal_email;

# a la taula "company"
ALTER TABLE company
DROP COLUMN website;

# a la taula "transaction"
ALTER TABLE transaction
MODIFY COLUMN credit_card_id VARCHAR(20);

# a la taula "credit_card"
ALTER TABLE credit_card
MODIFY COLUMN iban VARCHAR(50),
MODIFY COLUMN pin VARCHAR(4),
MODIFY COLUMN cvv INT,
MODIFY COLUMN expiring_date VARCHAR(20),
ADD COLUMN fecha_actual DATE;

# comprovant si hi ha dades no assignades (òrfenes) a la taula data_user
SELECT DISTINCT(t.user_id)
FROM transaction t 
LEFT JOIN data_user du ON t.user_id = du.id
WHERE du.id IS NULL;

# assignació de l'id corresponent de la taula de transactions (user_id)
INSERT INTO data_user (id) VALUES (9999);

# vinculem les taules data_user i transaction mitjançant PK-FK
ALTER TABLE transaction
ADD CONSTRAINT user_transaction
FOREIGN KEY (user_id)
REFERENCES data_user(id);

################### Exercici 2
# L'empresa també us demana crear una vista anomenada "InformeTecnico" que contingui la següent 
# informació:
-- ID de la transacció
-- Nom de l'usuari/ària
-- Cognom de l'usuari/ària
-- IBAN de la targeta de crèdit usada.
-- Nom de la companyia de la transacció realitzada.
-- Assegureu-vos d'incloure informació rellevant de les taules que coneixereu i utilitzeu àlies per 
-- canviar de nom columnes segons calgui.
# Mostra els resultats de la vista, ordena els resultats de forma descendent en funció de la variable 
# ID de transacció.

CREATE VIEW InformeTecnico AS
SELECT t.id				   AS Transaction_ID, 
	   du.name  	  	   AS First_Name, 
       du.surname 	  	   AS Given_Name, 
       cc.iban	  	  	   AS IBAN, 
       c.company_name 	   AS Company_Name
FROM transaction t
JOIN data_user du   ON du.id = t.user_id
JOIN credit_card cc ON cc.id = t.credit_card_id
JOIN company c      ON c.id = t.company_id
ORDER BY t.id DESC;

SELECT *
FROM InformeTecnico