# Float drifter iot edge device

## development

### simulator in ubuntu
start simulator 


docker w/o sudo
sudo setfacl -m user:$USER:rw /var/run/docker.sock 


'''
sudo env "PATH=$PATH" "iotedgehubdev" start -d "/home/jte/development/robo_float/config/deployment.debug.amd64.json" -v
'''

#docker 
various docker issues to be solved before push to registry worked

sudo usermod -a -G docker $USER

sudo chmod 666 /var/run/docker.sock

#troubleshoot
https://docs.microsoft.com/en-us/azure/iot-edge/troubleshoot

'''
sudo systemctl restart iotedge
'''


