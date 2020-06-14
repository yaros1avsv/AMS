import paramiko
import time


class Host:
	def __init__(self, hostname, username, password):
		self.hostname = hostname
		self.username = username
		self.password = password
		
		def connetion():
			try:
				ssh = paramiko.SSHClient()
				ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
				ssh.connect(hostname, username=username, password=password, timeout=5)
				print(f'Connected to {hostname}...')
			except paramiko.AuthenticationException:
				print(f'Failed to connect to {hostname} due to wrong username/password!')
				exit(1)
			except Exception as error:
				print(error.message)
				exit(2)
			
			return ssh
		
		self.connection = connetion()
	
	def executeCommand(self, command, sleep=3):
		try:
			stdin, stdout, stderr = self.connection.exec_command(f'sudo {command}', get_pty=True)
			stdin.write(self.password + '\n')
			stdin.flush()
			time.sleep(sleep)
		except Exception as error:
			print(error.message)
	
	def commandList(self, file, master='', slave='', arbiter=''):
		command = list()
		with open(f'{file}.txt', "rb") as file:
			for line in file:
				line = str(line)[2:-5].replace('\\t', '')
				line = line.replace('MASTER', master)
				line = line.replace('SLAVE', slave)
				line = line.replace('ARBITER', arbiter)
				command.append(line)
		return command
	
	def createBash(self, command, output):
		print(f'Generate {output}....\r')
		Host.executeCommand(self, f'rm -r {output}.sh')
		instruction = '\n'.join(command)
		Host.executeCommand(self, f'echo "{instruction}" > {output}.sh')
		Host.executeCommand(self, f'chmod +x {output}.sh')
		print(f'Generation complete {output}!')
	
	def runBash(self, file):
		print(f'Run {file}.sh...')
		Host.executeCommand(self, f'./{file}.sh', sleep=15)
		print(f'Run {file.replace("-Config", "Run")}.sh...')
		Host.executeCommand(self, f'./{file.replace("-Config", "Run")}.sh')


class Arbiter(Host):
	def __init__(self, hostname, username, password, master):
		super().__init__(hostname, username, password)
		self.master = master
		self.config = 'Arbiter-Config'
		self.run = 'ArbiterRun'
		self.command = self.commandList(self.config)
		self.createBash(self.command, self.config)
		self.command = self.commandList(self.run, master=self.master)
		self.createBash(self.command, self.run)


class Master(Host):
	def __init__(self, hostname, username, password, slave, arbiter):
		super().__init__(hostname, username, password)
		self.slave = slave
		self.arbiter = arbiter
		self.config = 'Master-Config'
		self.run = 'MasterRun'
		self.command = self.commandList(self.config, slave=self.slave, arbiter=self.arbiter, master=self.hostname)
		self.createBash(self.command, self.config)
		self.command = self.commandList(self.run, slave=self.slave, arbiter=self.arbiter, master=self.hostname)
		self.createBash(self.command, self.run)


class Slave(Host):
	def __init__(self, hostname, username, password, master, arbiter):
		super().__init__(hostname, username, password)
		self.config = 'Slave-Config'
		self.run = 'SlaveRun'
		self.master = master
		self.arbiter = arbiter
		self.command = self.commandList(self.config, master=self.master, arbiter=self.arbiter)
		self.createBash(self.command, self.config)
		self.command = self.commandList(self.run, arbiter=self.arbiter, master=self.master)
		self.createBash(self.command, self.run)


if __name__ == '__main__':
	a = Slave('192.168.149.155', 'student', '12345', '192.168.0.1', '192.168.0.3')