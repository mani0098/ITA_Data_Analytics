# Sprint 2
########## Nivell 1
################### Exercici 1
# A partir dels documents adjunts (estructura_dades and dades_introduir), importa les dues taules. Mostra les 
# característiques principals de l'esquema creat i explica les diferents taules i variables que existeixen. 
# Assegura't d'incloure un diagrama que il·lustri la relació entre les diferents taules i variables.

USE transactions;

SHOW tables;

DESCRIBE company;
DESCRIBE transaction;

SELECT *
FROM information_schema.TABLES 
WHERE table_schema = 'transactions';

SELECT TABLE_NAME,COLUMN_NAME,CONSTRAINT_NAME,
  REFERENCED_TABLE_NAME,
  REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'transactions'
  AND REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY TABLE_NAME, COLUMN_NAME;

SELECT TABLE_NAME,COLUMN_NAME,DATA_TYPE,IS_NULLABLE,COLUMN_KEY
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'transactions'
ORDER BY TABLE_NAME, ORDINAL_POSITION;

SELECT *
FROM transactions.company;

SELECT *
FROM transactions.transaction;

################### Exercici 2
# Utilitzant JOIN realitzaràs les següents consultes:

# 2.1. Llistat dels països que estan generant vendes.

SELECT DISTINCT c.country AS Country
FROM transaction t
JOIN company c ON c.id = t.company_id;

# 2.2. Des de quants països es generen les vendes.

SELECT COUNT(DISTINCT(c.country)) AS Country_Num
FROM transaction t
JOIN company c ON c.id = t.company_id;

# 2.3. Identifica la companyia amb la mitjana més gran de vendes.

SELECT c.company_name AS Company_Name, c.id AS Company_ID, ROUND(AVG(t.amount), 3) AS Average_Sale
FROM transaction t
JOIN company c ON c.id = t.company_id
GROUP BY c.company_name, c.id
ORDER BY Average_Sale DESC
LIMIT 1;

################### Exercici 3
# Utilitzant només subconsultes (sense utilitzar JOIN):

# 3.1. Mostra totes les transaccions realitzades per empreses d'Alemanya.

SELECT *
FROM transaction t
WHERE t.company_id IN (
					   SELECT c.id
					   FROM company c
					   WHERE c.country = 'Germany'
					  );

# 3.2. Llista les empreses que han realitzat transaccions per un amount superior a la mitjana de totes 
# les transaccions.

SELECT *
FROM company c
WHERE c.id IN (
			  SELECT t.company_id
			  FROM transaction t
			  WHERE t.amount > (
								SELECT AVG(t.amount) AS Average_Transactions
								FROM transaction t
                                )
			 );

# 3.3. Eliminaran del sistema les empreses que no tenen transaccions registrades, entrega el llistat 
# d'aquestes empreses.

SELECT *
FROM company c
WHERE NOT EXISTS (
				  SELECT 1
                  FROM transaction t
				  WHERE t.company_id = c.id
				 );
                 
########## Nivell 2
################### Exercici 1
# Identifica els cinc dies que es va generar la quantitat més gran d'ingressos a l'empresa per vendes. Mostra 
# la data de cada transacció juntament amb el total de les vendes.

# Primer enfoque
SELECT date(t.timestamp) AS Date, SUM(t.amount) AS Total_Sales
FROM transaction t
GROUP BY date(t.timestamp)
ORDER BY Total_Sales DESC
LIMIT 5;

# Segundo enfoque
SELECT c.company_name AS Company_Name, date(t.timestamp) AS Date, SUM(t.amount) AS Total_Sales
FROM transaction t
JOIN company c ON c.id = t.company_id
WHERE t.declined = 0
	  AND t.amount IS NOT NULL
      AND timestamp IS NOT NULL
GROUP BY c.company_name, date(t.timestamp)
ORDER BY Total_Sales DESC
LIMIT 5;

################### Exercici 2
# Quina és la mitjana de vendes per país? Presenta els resultats ordenats de major a menor mitjà.

SELECT c.country AS Country, ROUND(AVG(t.amount),3) AS Average
FROM transaction t
JOIN company c ON c.id = t.company_id
GROUP BY c.country
ORDER BY Average DESC;

################### Exercici 3
# En la teva empresa, es planteja un nou projecte per a llançar algunes campanyes publicitàries per a fer 
# competència a la companyia "Non Institute". Per a això, et demanen la llista de totes les transaccions 
# realitzades per empreses que estan situades en el mateix país que aquesta companyia.

# 3.1. Mostra el llistat aplicant JOIN i subconsultes.

SELECT t.*
FROM transaction t
JOIN company c ON c.id = t.company_id
WHERE c.country = (
					SELECT c1.country
                    FROM company c1
                    WHERE c1.company_name = 'Non Institute'
                    )
AND c.company_name <> 'Non Institute';

# Mostra el llistat aplicant solament subconsultes.

SELECT t.*
FROM transaction t
WHERE t.company_id NOT IN (
					       SELECT c.id
                           FROM company c
                           WHERE c.company_name = 'Non Institute'
                           )
AND t.company_id IN (
					 SELECT c1.id
					 FROM company c1
					 WHERE c1.country = (
										 SELECT c2.country
										 FROM company c2
										 WHERE c2.company_name = 'Non Institute'
										 )
					 );

########## Nivell 3
################### Exercici 1
# Presenta el nom, telèfon, país, data i amount, d'aquelles empreses que van realitzar transaccions amb un 
# valor comprès entre 350 i 400 euros i en alguna d'aquestes dates: 29 d'abril del 2015, 20 de juliol del 2018 
# i 13 de març del 2024. Ordena els resultats de major a menor quantitat.

SELECT c.company_name 	 AS Company_Name, 
	   c.phone 		  	 AS Phone_Number, 
       c.country 	  	 AS Country, 
       date(t.timestamp) AS Date, 
       t.amount			 AS Amount
FROM company c
JOIN transaction t ON t.company_id = c.id
WHERE t.amount BETWEEN 350 AND 400
AND date(t.timestamp) IN ('2015-04-29', '2018-07-20', '2024-03-13')
ORDER BY t.amount DESC;

################### Exercici 2
# Necessitem optimitzar l'assignació dels recursos i dependrà de la capacitat operativa que es requereixi, per 
# la qual cosa et demanen la informació sobre la quantitat de transaccions que realitzen les empreses, però el 
# departament de recursos humans és exigent i vol un llistat de les empreses on especifiquis si tenen més de 400 
# transaccions o menys.

SELECT c.company_name AS Company_Name, COUNT(t.id) AS Transactions_Num,
	   CASE WHEN COUNT(t.id) > 400 THEN 'More than 400'
       ELSE 'Less than 400'
       END AS Transaction_Category
FROM company c
JOIN transaction t ON t.company_id = c.id
GROUP BY c.company_name
ORDER BY Transactions_Num DESC;