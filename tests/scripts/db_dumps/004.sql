source 000.sql


-- MySQL dump 10.13  Distrib 8.1.0, for macos13.3 (arm64)
--
-- Host: localhost    Database: pypeal_test
-- ------------------------------------------------------
-- Server version	8.1.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Dumping data for table `associations`
--

LOCK TABLES `associations` WRITE;
/*!40000 ALTER TABLE `associations` DISABLE KEYS */;
INSERT INTO `associations` VALUES (234,'Australian and New Zealand Association'),(235,'Ancient Society of College Youths'),(236,'Bath and Wells Diocesan Association'),(237,'Bedfordshire Association'),(238,'Beverley and District Society'),(239,'Carlisle Diocesan Guild'),(240,'Central European Association'),(241,'Chester Diocesan Guild'),(242,'Coventry Diocesan Guild'),(243,'Cambridge University Guild'),(244,'Durham and Newcastle Diocesan Association'),(245,'Dorset County Association'),(246,'Derby Diocesan Association'),(247,'Devon Association'),(248,'East Cornwall Bellringers Association'),(249,'East Derbyshire and West Nottinghamshire Association'),(250,'East Grinstead and District Guild'),(251,'Ely Diocesan Association'),(252,'Essex Association'),(253,'Gloucester and Bristol Diocesan Association'),(254,'Guildford Diocesan Guild'),(255,'Guild of Devonshire Ringers'),(256,'Hertford County Association'),(257,'Hereford Diocesan Guild'),(258,'Irish Association'),(259,'Kent County Association'),(260,'Llandaff and Monmouth Diocesan Association'),(261,'Lancashire Association'),(263,'Leicester Diocesan Guild'),(264,'Ladies\' Guild'),(265,'Lincoln Diocesan Guild'),(266,'Liverpool Universities Society'),(267,'Lundy Island Society'),(268,'Lichfield and Walsall Archdeaconries Society'),(269,'Middlesex County Association and London Diocesan Guild'),(270,'North American Guild'),(271,'Norwich Diocesan Association'),(272,'North Staffordshire Association'),(273,'North Wales Association'),(274,'Oxford Diocesan Guild'),(275,'Oxford Society'),(276,'Oxford University Society'),(277,'Peterborough Diocesan Guild'),(278,'Swansea and Brecon Diocesan Guild'),(279,'South African Guild'),(280,'Salisbury Diocesan Guild'),(281,'Shropshire Association'),(282,'Scottish Association'),(283,'St Davids Diocesan Guild'),(284,'St Martin\'s Guild'),(285,'Society of Royal Cumberland Youths'),(286,'Suffolk Guild'),(287,'Surrey Association'),(288,'Sussex County Association'),(289,'Southwell and Nottingham Diocesan Guild'),(290,'Truro Diocesan Guild'),(292,'University of Bristol Society'),(293,'University of London Society'),(294,'Veronese Association'),(295,'Winchester and Portsmouth Diocesan Guild'),(296,'Worcestershire and Districts Association'),(297,'Yorkshire Association'),(298,'Zimbabwe Guild'),(299,'Manchester Universities Guild'),(424,'Leeds University Society');
/*!40000 ALTER TABLE `associations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `ringers`
--

LOCK TABLES `ringers` WRITE;
/*!40000 ALTER TABLE `ringers` DISABLE KEYS */;
INSERT INTO `ringers` VALUES (1,'Ferguson','Lydia',0,NULL),(2,'Gray','Harold',0,NULL),(3,'Henderson','Chloe',0,NULL),(4,'Henderson','Alen',0,NULL),(5,'Wright','Lucas',0,NULL),(6,'Farrell','Lucas',0,NULL),(7,'Elliott','Ryan',0,NULL),(8,'Harris','Ted',0,NULL),(9,'Casey','Dainton',0,NULL),(10,'Mason','Daryl',0,NULL),(11,'Clark','Roland',0,NULL),(12,'Thompson','Michelle',0,NULL),(13,'Rogers','David',0,NULL),(14,'Howard','Blake',0,NULL),(15,'Mitchell','Aston',0,NULL),(16,'Parker','John',0,NULL),(17,'Warren','Dominik',0,NULL),(18,'Murphy','Sienna',0,NULL),(19,'Mitchell','Aston',0,NULL),(20,'Evans','Melissa',0,NULL),(21,'Perkins','Valeria',0,NULL),(22,'Davis','Savana',0,NULL),(23,'Bailey','Fenton',0,NULL),(24,'Harper','Blake',0,NULL),(25,'Howard','Lenny',0,NULL);
/*!40000 ALTER TABLE `ringers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `peals`
--

LOCK TABLES `peals` WRITE;
/*!40000 ALTER TABLE `peals` DISABLE KEYS */;
INSERT INTO `peals` VALUES (1,22152,1,1,'2001-06-30',1,NULL,NULL,NULL,NULL,'S John Ev',NULL,NULL,1260,7,'Bob',0,NULL,NULL,NULL,'m12415','Grandsire Triples','Grandsire Triples',NULL,NULL,NULL,NULL,49,NULL,NULL,NULL,NULL,NULL),(2,1306360,2,1,'2019-10-17',2,NULL,NULL,236,NULL,'Blessed Virgin Mary',NULL,NULL,1260,5,NULL,0,5,1,3,NULL,'Mixed Doubles (5m/3v/1p)','Doubles (1p/5m/3v)',NULL,NULL,NULL,NULL,44,2352,'Eb',NULL,NULL,NULL),(3,1346767,2,1,'1963-03-25',3,NULL,NULL,286,NULL,'Holy Trinity',NULL,NULL,5040,6,'Surprise',0,8,0,0,NULL,'Mixed Surprise Minor (8m)','8 Methods Minor',NULL,NULL,NULL,NULL,162,1158,'G',NULL,NULL,NULL),(4,1425962,1,1,'2009-09-13',4,NULL,NULL,NULL,NULL,'S Peter',NULL,NULL,1260,7,'Bob',0,NULL,NULL,NULL,'m12415','Grandsire Triples','Grandsire Triples',NULL,NULL,NULL,NULL,45,1975,'E',NULL,NULL,NULL);
/*!40000 ALTER TABLE `peals` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `pealmethods`
--

LOCK TABLES `pealmethods` WRITE;
/*!40000 ALTER TABLE `pealmethods` DISABLE KEYS */;
INSERT INTO `pealmethods` VALUES (3,'m11104',NULL),(3,'m11121',NULL),(3,'m11349',NULL),(3,'m11369',NULL),(3,'m14317',NULL),(3,'m14563',NULL),(3,'m14568',NULL),(3,'m25915',NULL);
/*!40000 ALTER TABLE `pealmethods` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `pealringers`
--

LOCK TABLES `pealringers` WRITE;
/*!40000 ALTER TABLE `pealringers` DISABLE KEYS */;
INSERT INTO `pealringers` VALUES (1,1,1,5,0,NULL,NULL,NULL,NULL),(1,2,2,6,0,NULL,NULL,NULL,NULL),(1,3,3,7,0,NULL,NULL,NULL,NULL),(1,4,4,8,0,NULL,NULL,NULL,NULL),(1,5,5,9,0,NULL,NULL,NULL,NULL),(1,6,6,10,1,NULL,NULL,NULL,NULL),(1,7,7,11,0,NULL,NULL,NULL,NULL),(1,8,8,12,0,NULL,NULL,NULL,NULL),(2,8,5,5,1,NULL,NULL,NULL,NULL),(2,9,1,1,0,NULL,NULL,NULL,NULL),(2,10,2,2,0,NULL,NULL,NULL,NULL),(2,11,3,3,0,NULL,NULL,NULL,NULL),(2,12,4,4,0,NULL,NULL,NULL,NULL),(2,13,6,6,0,NULL,NULL,NULL,NULL),(3,4,4,4,0,NULL,NULL,NULL,NULL),(3,14,1,1,0,NULL,NULL,NULL,NULL),(3,15,2,2,0,NULL,NULL,NULL,NULL),(3,16,3,3,0,NULL,NULL,NULL,NULL),(3,17,5,5,0,NULL,NULL,NULL,NULL),(3,18,6,6,1,NULL,NULL,NULL,NULL),(4,17,2,4,0,NULL,NULL,NULL,NULL),(4,19,1,3,0,NULL,NULL,NULL,NULL),(4,20,3,5,0,NULL,NULL,NULL,NULL),(4,21,4,6,0,NULL,NULL,NULL,NULL),(4,22,5,7,0,NULL,NULL,NULL,NULL),(4,23,6,8,0,NULL,NULL,NULL,NULL),(4,24,7,9,1,NULL,NULL,NULL,NULL),(4,25,8,10,0,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `pealringers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `pealfootnotes`
--

LOCK TABLES `pealfootnotes` WRITE;
/*!40000 ALTER TABLE `pealfootnotes` DISABLE KEYS */;
INSERT INTO `pealfootnotes` VALUES (1,1,1,1,'First away from cover on 8.'),(1,2,4,4,'First of Grandsire inside.'),(3,1,NULL,NULL,'Rung as a wedding compliment to Miss Ann Pearce and Mr George Bradlaugh; Also a birthday compliment to Vernon B Bedford.'),(4,1,NULL,NULL,'For Evensong.');
/*!40000 ALTER TABLE `pealfootnotes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping data for table `pealphotos`
--

LOCK TABLES `pealphotos` WRITE;
/*!40000 ALTER TABLE `pealphotos` DISABLE KEYS */;
/*!40000 ALTER TABLE `pealphotos` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2023-11-23 18:30:59
