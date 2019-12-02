SET SQL_MODE="NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+07:00";

DROP TABLE IF EXISTS `cloud_variables`, `guests`, `guest_ip_pool`, `hosts`, `templates`, `lockedGuests`, `lockedHosts`, `tasks`, `hostLoad`, `guestLoad`;

CREATE TABLE IF NOT EXISTS `cloud_variables` (
  `key` varchar(255) NOT NULL,
  `value` text,
  PRIMARY KEY (`key`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

INSERT INTO `cloud_variables` (`key`, `value`) VALUES
('cloud_uuid', NULL),
('cloud_name', NULL),
('network_id', NULL),
('subnet_mask', NULL),
('default_route', NULL),
('dns_servers', NULL),
('global_lock','0'),
('auto_mode','0'),
('hold_all_log','0')
ON DUPLICATE KEY UPDATE `value`=NULL;

CREATE TABLE IF NOT EXISTS `guests` (
  `guestID` int(11) NOT NULL AUTO_INCREMENT,
  `guestName` varchar(255) DEFAULT NULL,
  `MACAddress` varchar(20) DEFAULT NULL,
  `IPAddress` varchar(16) DEFAULT NULL,
  `volumeFileName` text NOT NULL COMMENT 'image filename (abc.img)',
  `templateID` int(11) NOT NULL COMMENT 'ID of image template',
  `status` int(11) NOT NULL DEFAULT '0' COMMENT '0=shut off, 1=on, 2=saved',
  `activity` int(11) NOT NULL DEFAULT '0' COMMENT '0=none, 1=cloning, 2=booting, 3=saving, 4=restoring, 5=migrating',
  `lastHostID` int(11) DEFAULT NULL,
  `lastUUID` varchar(255) DEFAULT NULL,
  `memory` int(11) NOT NULL,
  `vCPU` int(11) NOT NULL,
  `inboundBandwidth` int(11) DEFAULT NULL,
  `outboundBandwidth` int(11) DEFAULT NULL,
  PRIMARY KEY (`guestID`),
  KEY `guestName` (`guestName`,`MACAddress`,`IPAddress`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

CREATE TABLE IF NOT EXISTS `guest_ip_pool` (
  `IPAddress` varchar(16) NOT NULL,
  PRIMARY KEY (`IPAddress`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `hosts` (
  `hostID` int(11) NOT NULL AUTO_INCREMENT,
  `hostName` varchar(255) NOT NULL,
  `MACAddress` varchar(20) NOT NULL,
  `IPAddress` varchar(16) NOT NULL,
  `isHost` int(11) NOT NULL DEFAULT '1' COMMENT '0=no ,1=yes',
  `isGlobalController` int(11) NOT NULL DEFAULT '0' COMMENT '0=no ,1=Master, 2=Slave',
  `isInformationServer` int(11) NOT NULL DEFAULT '0' COMMENT '0=no ,1=Master, 2=Slave',
  `isStorageHolder` int(11) NOT NULL DEFAULT '0' COMMENT '0=no ,1=Master, 2=Slave',
  `isCA` int(11) NOT NULL DEFAULT '0' COMMENT '0=no ,1=Master, 2=Slave',
  `status` int(11) NOT NULL DEFAULT '0' COMMENT '0=shutoff ,1=running, 2=suspend, 3=hibernated',
  `activity` int(11) NOT NULL DEFAULT '0' COMMENT '0=None ,1=evacuating, 2=opening',
  `cpuCore` tinyint(4) NOT NULL,
  `cpuSpeed` float NOT NULL COMMENT 'MHz (per core)',
  PRIMARY KEY (`hostID`),
  UNIQUE KEY `MACAddress` (`MACAddress`),
  UNIQUE KEY `IPAddress` (`IPAddress`),
  UNIQUE KEY `hostName` (`hostName`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

CREATE TABLE IF NOT EXISTS `templates` (
  `templateID` int(11) NOT NULL AUTO_INCREMENT,
  `fileName` varchar(255) NOT NULL COMMENT 'only file name, not path',
  `OS` varchar(255) NOT NULL,
  `size` bigint(20) NOT NULL COMMENT 'size of template image in bytes',
  `description` text NOT NULL,
  `minimumMemory` int(11) NOT NULL COMMENT 'megabyte',
  `maximumMemory` int(11) NOT NULL COMMENT 'megabyte',
  `activity` int(11) NOT NULL DEFAULT '0' COMMENT '0=none, 1=cloning',
  PRIMARY KEY (`templateID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

CREATE TABLE IF NOT EXISTS `lockedGuests` (
  `taskID` int(11) NOT NULL,
  `guestID` int(11) NOT NULL,
  PRIMARY KEY (`taskID`,`guestID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `lockedHosts` (
  `taskID` int(11) NOT NULL,
  `hostID` int(11) NOT NULL,
  PRIMARY KEY (`taskID`,`hostID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `tasks` (
  `taskID` int(11) NOT NULL AUTO_INCREMENT,
  `opcode` int(11) NOT NULL,
  `isMission` int(11) NOT NULL DEFAULT '0' COMMENT '0=primaryWork ,1=missionWork',
  `detail` text NOT NULL,
  `status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '0=inQueue ,1=working, 2=finish',
  `finishStatus` tinyint(4) NOT NULL DEFAULT '0' COMMENT '0=None ,1=success, 2=error',
  `finishMessage` text,
  `createTimestamp` datetime NOT NULL,
  `finishTimestamp` datetime DEFAULT NULL,
  `parentTaskID` int(11) DEFAULT NULL,
  `processID` int(11) DEFAULT NULL,
  PRIMARY KEY (`taskID`),
  KEY `status` (`status`,`createTimestamp`,`parentTaskID`)
) ENGINE=MyISAM  DEFAULT CHARSET=utf8 AUTO_INCREMENT=1 ;

CREATE TABLE IF NOT EXISTS `hostLoad` (
  `hostLoadID` int(11) NOT NULL AUTO_INCREMENT,
  `hostID` int(11) NOT NULL,
  `timestamp` double NOT NULL COMMENT 'sec',
  `idleTime` double NOT NULL COMMENT 'sec',
  `btime` int(11) NOT NULL,
  PRIMARY KEY (`hostLoadID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `guestLoad` (
  `guestLoadID` int(11) NOT NULL AUTO_INCREMENT,
  `guestID` int(11) NOT NULL,
  `timestamp` double NOT NULL COMMENT 'sec',
  `cpuTime` double NOT NULL COMMENT 'sec',
  PRIMARY KEY (`guestLoadID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `oldHostLoad` (
  `hostLoadID` int(11) NOT NULL,
  `hostID` int(11) NOT NULL,
  `timestamp` double NOT NULL COMMENT 'sec',
  `idleTime` double NOT NULL COMMENT 'sec',
  `btime` int(11) NOT NULL,
  PRIMARY KEY (`hostLoadID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `oldGuestLoad` (
  `guestLoadID` int(11) NOT NULL,
  `guestID` int(11) NOT NULL,
  `timestamp` double NOT NULL COMMENT 'sec',
  `cpuTime` double NOT NULL COMMENT 'sec',
  PRIMARY KEY (`guestLoadID`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
