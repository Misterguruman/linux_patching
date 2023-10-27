import paramiko
import os
import re
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

def log(log_level, message):
    """This will be replaced later with an external logging option shared by the whole product"""
    return

def send_command(ssh_client: paramiko.SSHClient, command:str) -> list[str] | None:
    """
    Wrapper to send ssh commands to a specified device. 
    Provides error handling and returns None on an unsuccessful command
    """
    _, ssh_stdout, ssh_stderr = ssh_client.exec_command(command=command)

    error = ssh_stderr.readlines()
    if error:
        log("ERROR", f"Error returned requesting '{command}': {error}")
        return None

    output = ssh_stdout.read()

    if not output: 
        log("ERROR", "Command ran successfully, but no output was returned")
        return None
    
    return output

def check_update(ssh_client: paramiko.SSHClient) -> tuple[list[str], list[str]] | None:
    """
    Runs the "sudo dnf check-update -d 0" on a remote machine.

    -d 0 eliminates cluttered output in stdout. 
    check-update will list available package upgrades on the device
    """
    command_output = send_command(ssh_client, "sudo dnf check-update -d 0")

    if not command_output:
        return None

    patches = [x.split()[0] for x in command_output.decode().split('\n') if x != '']
    obsoleting_position = patches.index("Obsoleting")
    available_patches = patches[0 : obsoleting_position]
    obsoleting_patches = patches[obsoleting_position+1 : ]

    return (available_patches, obsoleting_patches)

def get_dnf_configuration(ssh_client: paramiko.SSHClient) -> dict | None:
    """
    Return all option key/values from the /etc/dnf/dnf.conf file
    sudo cat /etc/dnf/dnf.conf
    """
    command_output = send_command(ssh_client, "sudo cat /etc/dnf/dnf.conf")

    if not command_output:
        return None

    configurations = [x for x in command_output.decode().split('\n') if x != '']

    configuration_scope = ""
    configuration_return_obj = {}
    for line in configurations:
        if re.match(r'\[.*\]', line):
            configuration_scope = line.replace('[','').replace(']','')
            configuration_return_obj[configuration_scope] = {}
            continue

        key, value = line.split('=')
        configuration_return_obj[configuration_scope][key] = value
        

    return configuration_return_obj

def get_package_exclusions():
    return

def add_package_exclusions():
    return

def compare_package_exclusions():
    return

if __name__ == '__main__':
    # IP Address/URL of the remote server
    server_address  = os.getenv("SERVER_ADDRESS")
    username        = os.getenv("SERVER_USERNAME")
    # Absolute path to .pem file for auth
    private_key     = os.getenv("PRIVATE_KEY")

    private_key = paramiko.RSAKey.from_private_key_file(private_key)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(server_address, username=username, pkey=private_key)

    check_update_output = check_update(ssh)

    if check_update_output:
        available_patches, obsoleting_patches = check_update_output
        print(f"Available Package Updates:\n {available_patches}")
        print(f"Obsoleting Package Updates:\n {obsoleting_patches}")

    dnf_configuration_output = get_dnf_configuration(ssh)

    if dnf_configuration_output:
        pprint(dnf_configuration_output)

    ssh.close()