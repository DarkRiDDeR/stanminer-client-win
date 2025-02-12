# Change Log
All notable changes to this project will be documented in this file.
 
The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).
 
## [Unreleased] - yyyy-mm-dd
 
Here we write upgrading notes 
 
### Added for new features
 
### Changed for changes in existing functionality

### Deprecated for soon-to-be removed features
 
### Removed for now removed features

### Fixed for any bug fixes

### Security in case of vulnerabilities

## [0.4.1-beta] - 2025-02-12

### Changed

change parametr ``user_threads`` set as optional

## [0.4.0-beta] - 2025-02-10

### Added

ability to loading only used miners

### Changed

- miners list moved from python code to config.ini
- console parameter *--worker* made required

### Removed

delete auto generation config.ini

## [0.3.1-beta] - 2025-02-08

### Changed
 
change run from bat script to run from powershell script

### Fixed

fix error "not recognized as an internal or external command,
operable program or batch file" for path with spaces

## [0.3.0-beta] - 2025-01-14

### Added

add detect hashrate for xmrig, cpuminer

### Fixed

fix kill processes of other miners

## [0.2.1-alpha] - 2024-11-02

### Fixed

fix detect temperature for some AMD CPU from Libre-hardware-monitor

## [0.2.0-alpha] - 2024-10-28

changed the start of mining via a subprocess in python

### Added

add debug mode

### Fixed

Fixed blocking of mining start by antivirus when an exception was added. Blocking occurred due to process launch via powershell. Now this happens through a subprocess in python

### Changed

delete parameter `hide_mining_window` for `config.ini`

## [0.1.1-alpha] - 2024-10-26
 
### Fixed

fix cpuminer-opt-rplant detect

## [0.1.0-alpha] - 2024-10-24
  
new stan-start client with the ability to switch between servers for mining different coins
 
### Added
 
 add miners:

- tnn-miner v0.4.4-r2 
- hellminer_avx2 v0.59.1

### Changed
  
update miners:

- binaryexpr v0.6.26
- cpuminer-opt-rplant v5.0.41
- srbminer-multi v2.6.9
- xmrig v6.22.1

 
