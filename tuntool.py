#!/usr/bin/python3

import os
import sys
import json
import subprocess 
import re

# Some globals.
BASE_DIRECTORY = os.path.dirname(os.path.realpath(__file__))
CONFIG_FILE_NAME = '.tuntool-conf'

DEFAULTS = {
    'ssh_host_ip': '',
    'ssh_user': ''
}

# Loads the config file. If the config file does not exist, then it creates one.
def load_config():
    if not os.path.isfile(BASE_DIRECTORY + '/' + CONFIG_FILE_NAME):
        print("Configuration file wasn't found. Generating one...")
        ssh_host_ip = input(
            'Enter the ssh host ip [' + DEFAULTS['ssh_host_ip'] + ']: '
        )
        ssh_host_ip = ssh_host_ip if ssh_host_ip.strip() != '' else DEFAULTS['ssh_host_ip']

        ssh_user = input(
            'Enter the ssh user [' + DEFAULTS['ssh_user'] + ']: '
        )
        ssh_user = ssh_user if ssh_user.strip() != '' else DEFAULTS['ssh_user']

        base_config = {
            'ssh_host_ip': ssh_host_ip,
            'ssh_user': ssh_user,

            'remotes': {}
        }

        #with open(BASE_DIRECTORY + '/' + CONFIG_FILE_NAME, 'w') as config_file:
        #    json.dump(base_config, config_file, indent=4, sort_keys=True)
        update_config(base_config)        

        return base_config
    else:
        config = {}
        with open(BASE_DIRECTORY + '/' + CONFIG_FILE_NAME) as config_file:
            config = json.load(config_file)
        
        return config


# Updates the config.
def update_config(config: dict):
    with open(BASE_DIRECTORY + '/' + CONFIG_FILE_NAME, 'w') as config_file:
        json.dump(config, config_file, indent=4, sort_keys=True)


# Gets the PID of a tunnel, returns false if the tunnel is not up..
def tunnel_pid(remote: dict):
    try:     
        subp = subprocess.check_output(
            'ps ax | grep [' + remote['local_port'] + ']:' + 
            remote['remote_host'] + ':' + remote['remote_port'],
            shell=True
        )
        pid = re.findall(r'\d+', str(subp.split(b'\n')[0].strip()))[0]
        return int(pid)
    except subprocess.CalledProcessError:
        return False

# Main function.
def main(args):
    try:
        config = load_config()    

        if 1 < len(args) and args[1] == 'add':
            values = [
                {
                    'name': 'remote name',
                    'key': 'remote_name',
                    'check_func': lambda value: value.strip() != ''
                },
                {
                    'name': 'local port',
                    'key': 'local_port',
                    'check_func': lambda value: value.isnumeric and value.strip() != ''
                },
                {
                    'name': 'remote host',
                    'key': 'remote_host',
                    'check_func': lambda value: value.strip() != ''
                },
                {
                    'name': 'remote port',
                    'key': 'remote_port',
                    'check_func': lambda value: value.isnumeric and value.strip() != ''
                }
            ]
            
            remote = {}
            remote_name = ''
            for value in values:
                inp = ''
                while not value['check_func'](inp):
                    inp = input('Enter ' + value['name'] + ': ')
                
                if value['key'] == 'remote_name':
                    remote_name = inp.strip()
                else:
                    remote[value['key']] = inp.strip()
            
            config['remotes'][remote_name] = remote
            update_config(config)

            print('Remote with name "' + remote_name + '" was successfully registered.')            

        elif 1 < len(args) and args[1] == 'status':
            print('Listing the registered remotes:')
            for k, v in config['remotes'].items():
                pid = tunnel_pid(v)
                print(
                    '\033[1;37m' + k + ': ' +
                    ('\033[0;32mOPENED' if pid != False else '\033[1;31mCLOSED')
                )

        elif 2 < len(args) and args[1] == 'open' and args[2].strip() != '':
            if args[2] not in config['remotes']:
                print('Remote "' + args[2] + '" was not found.')
                return
            
            remote = config['remotes'][args[2]]
            if tunnel_pid(remote) != False:
                print('Tunnel to remote "' + args[2] + '" is already open')
                return

            subprocess.call(
                'ssh -f -N -L ' + 
                    remote['local_port'] + ':' + remote['remote_host'] + ':' + remote['remote_port'] +
                    ' ' + config['ssh_user'] + '@' + config['ssh_host_ip'],
                shell=True
            )

            print('Tunnel to remote "' + args[2] + '" was successfully open.')
    
        elif 2 < len(args) and args[1] == 'close' and args[2].strip() != '':
            if args[2] not in config['remotes']:
                print('Remote "' + args[2] + '" was not found.')
                return
        
            remote = config['remotes'][args[2]]
            pid = tunnel_pid(remote)
            if pid == False:
                print('Tunnel to remote "' + args[2] + '" is not open.')            
                return

            subprocess.call(
                'kill ' + str(pid),
                shell=True
            )
            
            print('Tunnel to remote "' + args[2] + '" was successfully closed.')

    except KeyboardInterrupt:
        print('\nOperation interrupted.')

# Executing the main script and enemies of communism.
if __name__ == '__main__':
    main(sys.argv)

