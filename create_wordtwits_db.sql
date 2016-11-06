CREATE DATABASE  IF NOT EXISTS `WordTwitsDatabase` /*!40100 DEFAULT CHARACTER SET latin1 */;
USE `WordTwitsDatabase`;
-- MySQL dump 10.13  Distrib 5.7.12, for Win64 (x86_64)
--
-- Host: wordtwitsdb.chsq9glns06n.us-west-2.rds.amazonaws.com    Database: WordTwitsDatabase
-- ------------------------------------------------------
-- Server version	5.7.11

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `tickers`
--

DROP TABLE IF EXISTS `tickers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tickers` (
  `ticker` char(5) NOT NULL,
  `company_name` varchar(64) DEFAULT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `sector` varchar(64) DEFAULT NULL,
  `industry` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ticker_UNIQUE` (`ticker`),
  UNIQUE KEY `id_UNIQUE` (`id`),
  UNIQUE KEY `company_name_UNIQUE` (`company_name`)
) ENGINE=InnoDB AUTO_INCREMENT=13258 DEFAULT CHARSET=latin1 COMMENT='Dimension table for tickers';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `word_frequencies`
--

DROP TABLE IF EXISTS `word_frequencies`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `word_frequencies` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `ticker_id` int(11) NOT NULL,
  `word` varchar(32) NOT NULL,
  `frequency` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id_UNIQUE` (`id`),
  UNIQUE KEY `uq_ticker_idx` (`ticker_id`,`word`),
  KEY `fk_ticker_id_idx` (`ticker_id`),
  CONSTRAINT `fk_ticker_id` FOREIGN KEY (`ticker_id`) REFERENCES `tickers` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=latin1 COMMENT='Word Frequency fact table';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping routines for database 'WordTwitsDatabase'
--
/*!50003 DROP PROCEDURE IF EXISTS `update_word_frequencies` */;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8 */ ;
/*!50003 SET character_set_results = utf8 */ ;
/*!50003 SET collation_connection  = utf8_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
CREATE PROCEDURE `update_word_frequencies`(ticker_arg CHAR(5), word_arg VARCHAR(32), count_arg INT)
BEGIN

	# 1. Get ticker or insert
	INSERT IGNORE INTO tickers (ticker) VALUES(ticker_arg);

	# 2. Insert or add to word_frequencies
	INSERT INTO word_frequencies (ticker_id, word, frequency)
	VALUES ((SELECT id from tickers WHERE ticker=ticker_arg), word_arg, count_arg)
	ON DUPLICATE KEY UPDATE frequency = frequency + count_arg;
    
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2016-11-06 12:57:07
