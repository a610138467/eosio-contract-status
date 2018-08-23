#!/bin/bash

function start() {
    if [ -f './logs/pid.log' ];then
        pid=`cat ./logs/pid.log`
        process_num=`ps aux | grep $pid | grep -v grep | grep monitor.py | wc -l`
        if [ $process_num -eq 1 ];then
            echo "server already exists [pid=$pid]"
            return 1
        fi
    fi

    start_command="python server/monitor.py"
    $start_command
    
    pid=`cat ./logs/pid.log`
    process_num=`ps aux | grep $pid | grep -v grep | grep monitor.py | wc -l`
    if [ $process_num -eq 1 ]; then
        echo "start server success [pid=$pid]"
        return 0
    else
        echo "start server failed"
        return 1
    fi
}

function stop() {
    if [ -f './logs/pid.log' ];then
        pid=`cat ./logs/pid.log`
        process_num=`ps aux | grep $pid | grep -v grep | grep monitor.py | wc -l`
        if [ $process_num -eq 1 ]; then
            stop_command="kill $pid"
            $stop_command
            process_num=`ps aux | grep $pid | grep -v grep | grep monitor.py | wc -l`
            if [ $process_num -eq 0 ]; then
                echo "stop server success"
                rm -rf './logs/pid.log'
                return 0
            else
                echo "stop server failed [pid=$pid]"
                return 1
            fi
        else
            echo "server is not running"
            return 1
        fi
    else
        echo "server is not running"
        return 1
    fi
}

function status() {
    if [ -f './logs/pid.log' ];then
        pid=`cat ./logs/pid.log`
        process_num=`ps aux | grep $pid | grep -v grep | grep monitor.py | wc -l`
        if [ $process_num -eq 1 ]; then
            echo "server is running [pid=$pid]"
            return 0
        else
            echo "server stopped"
            return 1
        fi
    else
        echo "server stopped"
        return 1
    fi
}

case $1 in 
    "start")
        start
        exit
        break
        ;;
    "stop")
        stop
        exit
        break
        ;;
    "status")
        status
        exit
        break
        ;;
    *)
        echo "usages: sh control.sh [start|stop|status]"
        exit 1
        break
        ;;
esac
