
# connect hpf data1
cd /hpf/largeprojects/diagimage_common/
export TOKEN=771100
#nohup python /home/dsnider/hpf_static_server.py & # TODO: log rotate needed for nohup.out here
nohup sh -c 'while :; do python /home/dsnider/hpf_static_server.py; done > ~/hpf_static_server.log' &