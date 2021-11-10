#!/bin/bash

ATIME=$1
EMU=$2

pkill -9 -f ras_client-0.0.1-SNAPSHOT
pkill -9 -f ras_tier1-0.0.1-SNAPSHOT

java -jar ../ras_tier1/target/ras_tier1-0.0.1-SNAPSHOT-jar-with-dependencies.jar --cpuEmu $EMU &
java -jar ../ras_client/target/ras_client-0.0.1-SNAPSHOT-jar-with-dependencies.jar --atime $ATIME --threads 30 &

