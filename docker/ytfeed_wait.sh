#!/bin/bash
while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' localhost/backend)" != "200" ]]; do
    sleep 1;
done