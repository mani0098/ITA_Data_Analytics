# Sprint 4
########## Nivell 1
# Descàrrega els arxius CSV, estudia'ls i dissenya una base de dades amb un esquema d'estrella que 
# contingui, almenys 4 taules de les quals puguis realitzar les següents consultes:

-- Creació de la base de dades
CREATE DATABASE IF NOT EXISTS sprint4_bbdd;
USE sprint4_bbdd;

-- Creació de les taules
CREATE TABLE IF NOT EXISTS users (
								 id CHAR(10) PRIMARY KEY,
								 name VARCHAR(100),
								 surname VARCHAR(100),
								 phone VARCHAR(50),
								 email VARCHAR(255),
								 birth_date VARCHAR (50),
								 country VARCHAR(150),
								 city VARCHAR(150),
								 postal_code VARCHAR(100),
								 address VARCHAR(255)    
								 );

CREATE TABLE IF NOT EXISTS companies (
								     company_id VARCHAR(20) PRIMARY KEY,
								     company_name VARCHAR(255),
								     phone VARCHAR(50),
								     email VARCHAR(255),
								     country VARCHAR(150),
								     website VARCHAR(255)
								     );

CREATE TABLE IF NOT EXISTS credit_cards (
									    id VARCHAR(20) PRIMARY KEY,
									    user_id CHAR(10),
									    iban VARCHAR(40),
									    pan VARCHAR(20),
									    pin CHAR(5),
									    cvv CHAR(5),
									    track1 VARCHAR(100),
									    track2 VARCHAR(100),
									    expiring_date CHAR(20)
									    );

CREATE TABLE IF NOT EXISTS products (
									id VARCHAR(20) PRIMARY KEY,
									product_name VARCHAR(100),
									price VARCHAR(10),
									colour VARCHAR(50),
									weight DECIMAL(10, 2),
									warehouse_id VARCHAR(10)
								    );

CREATE TABLE IF NOT EXISTS transactions (
									    id VARCHAR(255) PRIMARY KEY,
									    card_id VARCHAR(20),
									    business_id VARCHAR(50),
									    timestamp TIMESTAMP,
									    amount DECIMAL(10, 2),
									    declined TINYINT,
									    product_ids VARCHAR(255),
									    user_id CHAR(10),
									    lat DOUBLE,
									    longitude DOUBLE
									    );

-- importar les dades del fitxer CSV
LOAD DATA 
INFILE 'D:/Spain/Online Courses/10. Data Analysis Specialization/1. SQL/Sprint 4/Assignment/american_users.csv'
INTO TABLE users
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

SHOW VARIABLES LIKE 'secure_file_priv';

LOAD DATA 
INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/Sprint_4_CSVs/american_users.csv'
INTO TABLE users
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;
    
LOAD DATA 
INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/Sprint_4_CSVs/european_users.csv'
INTO TABLE users
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA 
INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/Sprint_4_CSVs/companies.csv'
INTO TABLE companies
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA 
INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/Sprint_4_CSVs/credit_cards.csv'
INTO TABLE credit_cards
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA 
INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/Sprint_4_CSVs/products.csv'
INTO TABLE products
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

LOAD DATA 
INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/Sprint_4_CSVs/transactions.csv'
INTO TABLE transactions
FIELDS TERMINATED BY ';'	-- mostra un error si s'utilitza una coma
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS;

-- Canviar el nom d'algunes columnes per facilitar-ne l'ús posterior conservant el tipus de dada
ALTER TABLE transactions
CHANGE COLUMN business_id company_id VARCHAR(50);

ALTER TABLE transactions
CHANGE COLUMN product_ids products_id VARCHAR(255);

ALTER TABLE companies
CHANGE COLUMN company_id id VARCHAR(20);

ALTER TABLE companies
CHANGE COLUMN company_name name VARCHAR(255);

ALTER TABLE products
CHANGE COLUMN product_name name VARCHAR(100);

-- Vincular la taula de transactions (fet) amb altres taules mitjançant PK-FK
ALTER TABLE transactions
ADD FOREIGN KEY (card_id) REFERENCES credit_cards(id);

ALTER TABLE transactions
ADD FOREIGN KEY (company_id) REFERENCES companies(id);

ALTER TABLE transactions
ADD FOREIGN KEY (user_id) REFERENCES users(id);

ALTER TABLE credit_cards
ADD FOREIGN KEY (user_id) REFERENCES users(id);

-- Netejar les taules per facilitar l'ús posterior de les dades
SET SQL_SAFE_UPDATES=0;

UPDATE users 
SET birth_date = STR_TO_DATE(birth_date, '%b %d, %Y');

UPDATE credit_cards
SET expiring_date = STR_TO_DATE(expiring_date, '%m/%d/%y');

UPDATE products 
SET price = REPLACE(price,'$', '');

SET SQL_SAFE_UPDATES=1;

################### Exercici 1
# Realitza una subconsulta que mostri tots els usuaris amb més de 80 transaccions utilitzant almenys 2 
# taules.

SELECT *
FROM users u
WHERE u.id IN (
			   SELECT t.user_id AS User_ID
			   FROM transactions t
			   WHERE t.declined = 0
			   GROUP BY t.user_id
			   HAVING COUNT(*) > 80
               );


################### Exercici 2
# Mostra la mitjana d'amount per IBAN de les targetes de crèdit a la companyia Donec Ltd, utilitza 
# almenys 2 taules.

SELECT cc.iban AS IBAN,
       ROUND(AVG(t.amount), 3) AS Average_Amount
FROM transactions t
JOIN credit_cards cc ON cc.id = t.card_id
JOIN companies c ON c.id = t.company_id
WHERE c.name = 'Donec Ltd'
	  AND t.declined = 0
GROUP BY IBAN
ORDER BY Average_Amount DESC;

########## Nivell 2
# Crea una nova taula que reflecteixi l'estat de les targetes de crèdit basat en si les tres últimes 
# transaccions han estat declinades aleshores és inactiu, si almenys una no és rebutjada aleshores és 
# actiu. Partint d’aquesta taula respon:

CREATE TABLE IF NOT EXISTS Credit_Card_Status AS
SELECT card_id AS Card_ID,
	   CASE WHEN SUM(declined) = 3 THEN 'Inactive'
	   ELSE 'Active'
	   END AS Recent_Status
FROM (SELECT card_id,
			 declined,
		     ROW_NUMBER() 
             OVER(
				  PARTITION BY card_id
				  ORDER BY DATE(timestamp) DESC
				  ) AS Sort_Order
	  FROM transactions) t
WHERE Sort_Order <= 3
GROUP BY Card_ID;

################### Exercici 1
# Quantes targetes estan actives?

SELECT COUNT(Recent_Status) AS Active_Cards
FROM Credit_Card_Status
WHERE Recent_Status = "Active";

########## Nivell 3
# Crea una taula amb la qual puguem unir les dades del nou arxiu products.csv amb la base de dades 
# creada, tenint en compte que des de transaction tens product_ids. Genera la següent consulta:

CREATE TABLE IF NOT EXISTS Prod_Trans_Bridge (
											  transaction_id VARCHAR(255),
											  product_id VARCHAR(20),
											  PRIMARY KEY (transaction_id, product_id),
											  FOREIGN KEY (transaction_id) REFERENCES transactions(id),
											  FOREIGN KEY (product_id) REFERENCES products(id)
											  );

UPDATE transactions
SET products_id = CAST(CONCAT('["', REPLACE(products_id, ', ', '","'), '"]') AS JSON);

INSERT INTO Prod_Trans_Bridge (transaction_id, product_id)
SELECT transactions.id AS transaction_id, 
	   js.product_id AS product_id
FROM transactions, 
	 JSON_TABLE(
				transactions.products_id,'$[*]' COLUMNS (product_id VARCHAR(20) PATH '$')
                ) AS js;

################### Exercici 1
# Necessitem conèixer el nombre de vegades que s'ha venut cada producte.

SELECT p.id AS Product_ID, 
	   p.name Product_Name, 
       COUNT(ptb.product_id) AS Sold_Count
FROM Prod_Trans_Bridge ptb
JOIN products p
ON ptb.product_id = p.id
JOIN transactions t
ON t.id = ptb.transaction_id
WHERE t.declined = 0
AND t.products_id IS NOT NULL
AND t.products_id <> ''
GROUP BY p.id, p.name
ORDER BY p.id;