import paramiko
import os
# import logging
from dotenv import load_dotenv

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
    Runs the "sudo dnf check-update" on a remote machine.
    """
    output = send_command(ssh_client, "sudo dnf check-update")

    if not output:
        return None

    patches = [x.split()[0] for x in output.decode().split('\n\n')[-1].split('\n') if x != '']
    obsoleting_position = patches.index("Obsoleting")
    available_patches = patches[0 : obsoleting_position]
    obsoleting_patches = patches[obsoleting_position+1 : ]

    return (available_patches, obsoleting_patches)

if __name__ == '__main__':
    server_address  = os.getenv("SERVER_ADDRESS")
    username        = os.getenv("USERNAME")
    private_key     = os.getenv("PRIVATE_KEY")

    private_key = paramiko.RSAKey.from_private_key_file(private_key)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(server_address, username=username, pkey=private_key)

    command_output = check_update(ssh)

    ssh.close()