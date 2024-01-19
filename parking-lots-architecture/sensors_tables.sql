CREATE TABLE `messages` (
  `time` datetime NOT NULL,
  `park_id` varchar(20) NOT NULL DEFAULT '0',
  `dev_eui` varchar(16) NOT NULL,
  `seqno` int(11) NOT NULL,
  `msg_type` varchar(10) NOT NULL,
  `state` tinyint(1) NOT NULL,
  `payload` varchar(40) DEFAULT NULL,
  PRIMARY KEY (`time`,`dev_eui`,`seqno`,`park_id`),
  KEY `ix_messages_time` (`time`),
  KEY `messages_park_id_fk_idx` (`park_id`),
  CONSTRAINT `messages_park_id_fk` FOREIGN KEY (`park_id`) REFERENCES `parcheggio` (`idparch`)
);

CREATE TABLE `occupancy` (
  `time` datetime NOT NULL,
  `park_id` varchar(20) NOT NULL DEFAULT '0',
  `percentage` double DEFAULT NULL,
  PRIMARY KEY (`time`,`park_id`),
  KEY `ix_occupancy_time` (`time`),
  KEY `occupancy_park_id_fk_idx` (`park_id`),
  CONSTRAINT `occupancy_park_id_fk` FOREIGN KEY (`park_id`) REFERENCES `parcheggio` (`idparch`)
);