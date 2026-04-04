#!/bin/bash
#
# Title:add_port1.sh
# Description:
# Development Environment: OS X 10.15.2/postgres 12.12
# Author: G.S. Cole (guy at shastrax dot com)
#
# psql -U polaris_admin -d polaris
#
export PGDATABASE=polaris
export PGHOST=localhost
export PGPASSWORD=woofwoof
export PGUSER=polaris_admin
#
psql -d $PGDATABASE -U $PGUSER -c "insert into polaris_port(port_code, port_name, scrape_flag, url) values('USPDX002', 'Portland', false, 'https://www.vesselfinder.com/ports/USPDX002');"
psql -d $PGDATABASE -U $PGUSER -c "insert into polaris_port(port_code, port_name, scrape_flag, url) values('USVAN001', 'Vancouver', false, 'https://www.vesselfinder.com/ports/USVAN001');"
psql -d $PGDATABASE -U $PGUSER -c "insert into polaris_port(port_code, port_name, scrape_flag, url) values('PAPXX001', 'Pena Blanca Anchorage', false, 'https://www.vesselfinder.com/ports/PAPXX001');"
psql -d $PGDATABASE -U $PGUSER -c "insert into polaris_port(port_code, port_name, scrape_flag, url) values('USSEA001', 'Seattle', false, 'https://www.vesselfinder.com/ports/USSEA001');"
psql -d $PGDATABASE -U $PGUSER -c "insert into polaris_port(port_code, port_name, scrape_flag, url) values('USTIW001', 'Tacoma', false, 'https://www.vesselfinder.com/ports/USTIW001');"
psql -d $PGDATABASE -U $PGUSER -c "insert into polaris_port(port_code, port_name, scrape_flag, url) values('USLAX001', 'Los Angeles', false, 'https://www.vesselfinder.com/ports/USLAX001');"
psql -d $PGDATABASE -U $PGUSER -c "insert into polaris_port(port_code, port_name, scrape_flag, url) values('USHNL001', 'Honolulu', false, 'https://www.vesselfinder.com/ports/USHNL001');"
psql -d $PGDATABASE -U $PGUSER -c "insert into polaris_port(port_code, port_name, scrape_flag, url) values('KRBNP001', 'Busan', false, 'https://www.vesselfinder.com/ports/KRBNP001');"
psql -d $PGDATABASE -U $PGUSER -c "insert into polaris_port(port_code, port_name, scrape_flag, url) values('PAPCN006', 'Panama Canal', false, 'https://www.vesselfinder.com/ports/PAPCN006');"
psql -d $PGDATABASE -U $PGUSER -c "insert into polaris_port(port_code, port_name, scrape_flag, url) values('NLRTM001', 'Rotterdam', false, 'https://www.vesselfinder.com/ports/NLRTM001');"
psql -d $PGDATABASE -U $PGUSER -c "insert into polaris_port(port_code, port_name, scrape_flag, url) values('HKHKG001', 'Hong Kong', false, 'https://www.vesselfinder.com/ports/HKHKG001');"
psql -d $PGDATABASE -U $PGUSER -c "insert into polaris_port(port_code, port_name, scrape_flag, url) values('JPYAT001', 'Yatsushiro', false, 'https://www.vesselfinder.com/ports/JPYAT001');"
psql -d $PGDATABASE -U $PGUSER -c "insert into polaris_port(port_code, port_name, scrape_flag, url) values('MXTPB001', 'Topolobampo', false, 'https://www.vesselfinder.com/ports/MXTPB001');"
psql -d $PGDATABASE -U $PGUSER -c "insert into polaris_port(port_code, port_name, scrape_flag, url) values('TWKHH001', 'Kaohsiung', false, 'https://www.vesselfinder.com/ports/TWKHH001');"
psql -d $PGDATABASE -U $PGUSER -c "insert into polaris_port(port_code, port_name, scrape_flag, url) values('JPTMK001', 'Tomakomai', false, 'https://www.vesselfinder.com/ports/JPTMK001');"
psql -d $PGDATABASE -U $PGUSER -c "insert into polaris_port(port_code, port_name, scrape_flag, url) values('MYBTU001', 'Bintulu', false, 'https://www.vesselfinder.com/ports/MYBTU001');"
psql -d $PGDATABASE -U $PGUSER -c "insert into polaris_port(port_code, port_name, scrape_flag, url) values('JPSKD001', 'Sakaide', false, 'https://www.vesselfinder.com/ports/JPSKD001');"
psql -d $PGDATABASE -U $PGUSER -c "insert into polaris_port(port_code, port_name, scrape_flag, url) values('JPSAK001', 'Sakai', false, 'https://www.vesselfinder.com/ports/JPSAK001');"
psql -d $PGDATABASE -U $PGUSER -c "insert into polaris_port(port_code, port_name, scrape_flag, url) values('KRMAS001', 'Masan', false, 'https://www.vesselfinder.com/ports/KRMAS001');"
psql -d $PGDATABASE -U $PGUSER -c "insert into polaris_port(port_code, port_name, scrape_flag, url) values('KRUSN001', 'Ulsan', false, 'https://www.vesselfinder.com/ports/KRUSN001');"
#
