#/bin/bash

curl -G http://influxdb:8086/query --data-urlencode "q=CREATE DATABASE lazybot"
lazy-bot-tester-collecter
