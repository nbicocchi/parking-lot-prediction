
--
-- Database: `parcheggi`
--

-- --------------------------------------------------------

--
-- Struttura della tabella `arc`
--

CREATE TABLE `arc` (
  `idParch` varchar(20) NOT NULL,
  `idNode` varchar(20) NOT NULL,
  `idArc` varchar(20) NOT NULL,
  `target` varchar(20) NOT NULL,
  `weight` int(11) DEFAULT 0
);

-- --------------------------------------------------------

--
-- Struttura della tabella `citta`
--

CREATE TABLE `citta` (
  `nome` varchar(30) NOT NULL,
  `latitudine` double NOT NULL,
  `longitudine` double NOT NULL
);

-- --------------------------------------------------------

--
-- Struttura della tabella `node`
--

CREATE TABLE `node` (
  `idParch` varchar(20) NOT NULL,
  `idNode` varchar(20) NOT NULL,
  `posX` int(11) NOT NULL,
  `posY` int(11) NOT NULL
);

-- --------------------------------------------------------

--
-- Struttura della tabella `parcheggio`
--

CREATE TABLE `parcheggio` (
  `idParch` varchar(20) NOT NULL,
  `nome` varchar(30) NOT NULL,
  `totParkNum` int(11) DEFAULT NULL,
  `citta` varchar(20) NOT NULL,
  `via` varchar(30) NOT NULL,
  `numero` int(11) NOT NULL,
  `cap` varchar(10) NOT NULL,
  `provincia` char(2) NOT NULL,
  `tariffa` float NOT NULL,
  `controllato` bit(1) NOT NULL,
  `latitude` double NOT NULL,
  `longitude` double NOT NULL
);

-- --------------------------------------------------------

--
-- Struttura della tabella `park`
--

CREATE TABLE `park` (
  `idParch` varchar(20) NOT NULL,
  `idPark` varchar(20) NOT NULL,
  `posX` int(11) DEFAULT NULL,
  `posY` int(11) DEFAULT NULL,
  `type` int(11) DEFAULT NULL,
  `distanceEntr` int(11) DEFAULT NULL,
  `taken` bit(1) DEFAULT NULL
);

-- --------------------------------------------------------

--
-- Struttura della tabella `persona`
--

CREATE TABLE `persona` (
  `cf` char(16) NOT NULL,
  `email` varchar(50) NOT NULL,
  `nome` varchar(20) NOT NULL,
  `cognome` varchar(20) NOT NULL,
  `cellulare` varchar(20) NOT NULL,
  `data_nascita` date NOT NULL
);

-- --------------------------------------------------------

--
-- Struttura della tabella `preferiti`
--

CREATE TABLE `preferiti` (
  `email` varchar(50) NOT NULL,
  `idParch` varchar(20) NOT NULL
);

-- --------------------------------------------------------

--
-- Struttura della tabella `sostaattiva`
--

CREATE TABLE `sostaattiva` (
  `idParch` varchar(20) NOT NULL,
  `idPark` varchar(20) NOT NULL,
  `targa` char(7) NOT NULL,
  `email` varchar(50) NOT NULL,
  `dataInizio` datetime NOT NULL,
  `tariffa` float NOT NULL
);

-- --------------------------------------------------------

--
-- Struttura della tabella `sostachiusa`
--

CREATE TABLE `sostachiusa` (
  `idParch` varchar(20) NOT NULL,
  `idPark` varchar(20) NOT NULL,
  `targa` char(7) NOT NULL,
  `email` varchar(50) NOT NULL,
  `dataInizio` datetime NOT NULL,
  `dataFine` datetime DEFAULT NULL,
  `tariffa` float NOT NULL,
  `costo` float DEFAULT NULL
);

-- --------------------------------------------------------

--
-- Struttura della tabella `utente`
--

CREATE TABLE `utente` (
  `email` varchar(50) NOT NULL,
  `passwd` varchar(44) NOT NULL,
  `salt` varchar(30) NOT NULL
);

-- --------------------------------------------------------

--
-- Struttura della tabella `veicolo`
--

CREATE TABLE `veicolo` (
  `targa` char(7) NOT NULL,
  `marca` varchar(20) NOT NULL,
  `modello` varchar(20) NOT NULL,
  `tipo` int(1) NOT NULL,
  `parcheggiata` bit(1) NOT NULL,
  `email` varchar(50) NOT NULL
);

--
-- Indici per le tabelle scaricate
--

--
-- Indici per le tabelle `arc`
--
ALTER TABLE `arc`
  ADD PRIMARY KEY (`idParch`,`idNode`,`idArc`),
  ADD UNIQUE KEY `idParch` (`idParch`,`idNode`,`idArc`);

--
-- Indici per le tabelle `citta`
--
ALTER TABLE `citta`
  ADD PRIMARY KEY (`nome`);

--
-- Indici per le tabelle `node`
--
ALTER TABLE `node`
  ADD PRIMARY KEY (`idParch`,`idNode`),
  ADD UNIQUE KEY `idParch` (`idParch`,`idNode`);

--
-- Indici per le tabelle `parcheggio`
--
ALTER TABLE `parcheggio`
  ADD PRIMARY KEY (`idParch`),
  ADD KEY `parch_ibfk_1` (`citta`);

--
-- Indici per le tabelle `park`
--
ALTER TABLE `park`
  ADD PRIMARY KEY (`idParch`,`idPark`),
  ADD UNIQUE KEY `idParch` (`idParch`,`idPark`);

--
-- Indici per le tabelle `persona`
--
ALTER TABLE `persona`
  ADD PRIMARY KEY (`cf`),
  ADD KEY `persona_ibfk_1` (`email`);

--
-- Indici per le tabelle `preferiti`
--
ALTER TABLE `preferiti`
  ADD UNIQUE KEY `email` (`email`,`idParch`),
  ADD KEY `preferiti_ibfk_2` (`idParch`);

--
-- Indici per le tabelle `sostaattiva`
--
ALTER TABLE `sostaattiva`
  ADD PRIMARY KEY (`targa`,`email`),
  ADD KEY `sostaattiva_ibfk_1` (`idParch`,`idPark`),
  ADD KEY `sostaattiva_ibfk_3` (`email`);

--
-- Indici per le tabelle `sostachiusa`
--
ALTER TABLE `sostachiusa`
  ADD PRIMARY KEY (`targa`,`dataInizio`),
  ADD KEY `sostachiusa_ibfk_1` (`idParch`,`idPark`),
  ADD KEY `sostachiusa_ibfk_3` (`email`);

--
-- Indici per le tabelle `utente`
--
ALTER TABLE `utente`
  ADD PRIMARY KEY (`email`);

--
-- Indici per le tabelle `veicolo`
--
ALTER TABLE `veicolo`
  ADD PRIMARY KEY (`targa`),
  ADD KEY `veicolo_ibfk_1` (`email`);

--
-- Limiti per le tabelle scaricate
--

--
-- Limiti per la tabella `arc`
--
ALTER TABLE `arc`
  ADD CONSTRAINT `arc_ibfk_1` FOREIGN KEY (`idParch`,`idNode`) REFERENCES `node` (`idParch`, `idNode`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Limiti per la tabella `node`
--
ALTER TABLE `node`
  ADD CONSTRAINT `node_ibfk_1` FOREIGN KEY (`idParch`) REFERENCES `parcheggio` (`idParch`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Limiti per la tabella `parcheggio`
--
ALTER TABLE `parcheggio`
  ADD CONSTRAINT `parch_ibfk_1` FOREIGN KEY (`citta`) REFERENCES `citta` (`nome`) ON DELETE NO ACTION ON UPDATE CASCADE;

--
-- Limiti per la tabella `park`
--
ALTER TABLE `park`
  ADD CONSTRAINT `park_ibfk_1` FOREIGN KEY (`idParch`) REFERENCES `parcheggio` (`idParch`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Limiti per la tabella `persona`
--
ALTER TABLE `persona`
  ADD CONSTRAINT `persona_ibfk_1` FOREIGN KEY (`email`) REFERENCES `utente` (`email`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Limiti per la tabella `preferiti`
--
ALTER TABLE `preferiti`
  ADD CONSTRAINT `preferiti_ibfk_1` FOREIGN KEY (`email`) REFERENCES `persona` (`email`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `preferiti_ibfk_2` FOREIGN KEY (`idParch`) REFERENCES `parcheggio` (`idParch`) ON DELETE NO ACTION ON UPDATE CASCADE;

--
-- Limiti per la tabella `sostaattiva`
--
ALTER TABLE `sostaattiva`
  ADD CONSTRAINT `sostaattiva_ibfk_2` FOREIGN KEY (`targa`) REFERENCES `veicolo` (`targa`) ON UPDATE CASCADE,
  ADD CONSTRAINT `sostaattiva_ibfk_3` FOREIGN KEY (`email`) REFERENCES `persona` (`email`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Limiti per la tabella `sostachiusa`
--
ALTER TABLE `sostachiusa`
  ADD CONSTRAINT `sostachiusa_ibfk_2` FOREIGN KEY (`targa`) REFERENCES `veicolo` (`targa`) ON DELETE NO ACTION ON UPDATE CASCADE,
  ADD CONSTRAINT `sostachiusa_ibfk_3` FOREIGN KEY (`email`) REFERENCES `persona` (`email`) ON DELETE CASCADE ON UPDATE CASCADE;

--
-- Limiti per la tabella `veicolo`
--
ALTER TABLE `veicolo`
  ADD CONSTRAINT `veicolo_ibfk_1` FOREIGN KEY (`email`) REFERENCES `persona` (`email`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;
