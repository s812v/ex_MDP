A=$(ps -aux | grep rfcomm | grep root)
B=$(echo $A | cut -d " " -f 2)
echo "Killing $B"
kill -9 $B
bdaddr -i hci0 28:28:28:28:28:28
hciconfig hci0 reset
systemctl restart bluetooth.service