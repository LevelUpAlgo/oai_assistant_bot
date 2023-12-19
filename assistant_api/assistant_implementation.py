#!/usr/bin/env conda activate whopo
from abc import ABC, abstractmethod
from openai import OpenAI
from rich.console import Console
from rich.table import Table
from rich import box, pretty, print
import os, zipfile
import os
import zipfile
import chardet
import uuid
from rich import print as rprint
from rich.console import Console


pretty.install()

class IConsoleManager(ABC):
	@abstractmethod
	def print(self, message, style=None):
		pass

	@abstractmethod
	def add_row_to_table(self, row):
		pass

	@abstractmethod
	def print_table(self):
		pass

class ConsoleManager(IConsoleManager):
	def __init__(self):
		self.console = Console(
			width=100,
			color_system="auto",
			force_terminal=True,
			legacy_windows=False,
			record=True,
			markup=True,
			emoji=True,
			highlight=True,
			log_time_format="[%X]",
			log_path=False,
			soft_wrap=True,
			no_color=False,
			style="none",
			tab_size=4,
			_environ=os.environ,
		)
		self.table = Table(title="Assistants", box=box.DOUBLE_EDGE)
		self.table.add_column("ID", justify="right", style="cyan", no_wrap=True)
		self.table.add_column("Name", style="magenta")
		self.table.add_column("Description", style="cyan")
		self.table.add_column("Status", justify="right", style="green")
		self.table.add_column("Model", justify="right", style="yellow")
		self.table.add_column("Created At", justify="right", style="blue")

	def print(self, message, style=None):
		self.console.print(message, style=style)

	def add_row_to_table(self, row):
		self.table.add_row(*row)

	def print_table(self):
		self.console.print(self.table)

class IOpenAIManager(ABC):
	@abstractmethod
	def __init__(self):
		pass

class OpenAIManager(IOpenAIManager):
	def __init__(self):
		self.client = OpenAI()

class IAssistant(ABC):
	@abstractmethod
	def __init__(self, client, assistant_id):
		pass

	@abstractmethod
	def retrieve_assistant(self):
		pass

	@abstractmethod
	def update_assistant(self, file_ids):
		pass

class Assistant(IAssistant):
	def __init__(self, client, assistant_id):
		self.client = client
		self.assistant_id = assistant_id
		self.assistant = self.retrieve_assistant()

	def retrieve_assistant(self):
		assistant = self.client.beta.assistants.retrieve(self.assistant_id)
		return {_: my_assistant for _, my_assistant in assistant}

	def update_assistant(self, file_ids):
		return self.client.beta.assistants.update(self.assistant["id"], file_ids=file_ids)

class IFile(ABC):
	@abstractmethod
	def __init__(self, client, filepath, purpose):
		pass

	@abstractmethod
	def create_file(self):
		pass

class File(IFile):
	def __init__(self, client, filepath, purpose):
		self.client = client
		self.filepath = filepath
		self.purpose = purpose
		self.file_object = self.create_file()

	def create_file(self):
		with open(self.filepath, 'rb') as file:
			return self.client.files.create(file=file, purpose=self.purpose)

def zip_directory(directory_path, zip_file_name):
	with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
		for root, dirs, files in os.walk(directory_path):
			if 'node_modules' in dirs:
				dirs.remove('node_modules')  # don't visit node_modules directories
			for file in files:
				file_path = os.path.join(root, file)
				zipf.write(file_path, os.path.relpath(file_path, os.path.join(directory_path, '..')))

class IThread(ABC):
	@abstractmethod
	def __init__(self, client):
		pass

	@abstractmethod
	def create_thread(self):
		pass

class Thread(IThread):
	def __init__(self, client):
		self.client = client
		self.thread = self.create_thread()

	def create_thread(self):
		return self.client.beta.threads.create()

class IMessage(ABC):
	@abstractmethod
	def __init__(self, client, thread_id, file_ids, role, content):
		pass

	@abstractmethod
	def create_message(self):
		pass

	@abstractmethod
	def retrieve_message(self, message_id):
		pass

class Message(IMessage):
	def __init__(self, client, thread_id, file_ids, role, content):
		self.client = client
		self.thread_id = thread_id
		self.file_ids = file_ids
		self.role = role
		self.content = content
		self.thread_message = self.create_message()

	def create_message(self):
		return self.client.beta.threads.messages.create(
			thread_id=self.thread_id,
			file_ids=self.file_ids,
			role=self.role,
			content=self.content,
		)

	def retrieve_message(self, message_id):
		return self.client.beta.threads.messages.retrieve(
			message_id=message_id,
			thread_id=self.thread_id,
		)

class IRunStepDetailsPrinter(ABC):
	@abstractmethod
	def __init__(self, console_manager):
		pass

	@abstractmethod
	def print_run_step_details(self, run_steps):
		pass

class RunStepDetailsPrinter(IRunStepDetailsPrinter):
	def __init__(self, console_manager):
		self.console_manager = console_manager

	def print_run_step_details(self, run_steps):
		for run_step in run_steps.data:
			self.console_manager.print(f"Status: {run_step.status}")

			if run_step.step_details is not None:
				self.console_manager.print("Tool calls:")
				for tool_call in run_step.step_details:
					self.console_manager.print(tool_call)
					try:
						if tool_call.code_interpreter is not None:
							self.console_manager.print(f"Input: {tool_call.code_interpreter.input}")
							for output in tool_call.code_interpreter.outputs:
								self.console_manager.print(f"Output: {output.logs}")

					except AttributeError:
						pass

class IFileDownloader(ABC):
	@abstractmethod
	def __init__(self, client):
		pass

	@abstractmethod
	def download_file(self, file_id, output_path):
		pass

class FileDownloader(IFileDownloader):
	def __init__(self, client):
		self.client = client

	def download_file(self, file_id, output_path):
		info = self.client.files.content(file_id)
		info.stream_to_file(output_path)

# Usage
console_manager = ConsoleManager()
openai_manager = OpenAIManager()
run_step_details_printer = RunStepDetailsPrinter(console_manager)
file_downloader = FileDownloader(openai_manager.client)

assistant = Assistant(openai_manager.client, "asst_M8rgFTKZWASS1T40IplYycHb")

console_manager.add_row_to_table([
	assistant.assistant["id"],
	assistant.assistant["name"],
	assistant.assistant.get("description", "No description"),
	"Active" if assistant.assistant["tools"] else "Inactive",
	assistant.assistant["model"],
	str(assistant.assistant["created_at"]),
])
console_manager.print_table()

# Zip the directory
def zip_directory(directory_path, zip_path):
	zip_file_name = f'my_directory_{str(uuid.uuid4())}.zip'
	zip_directory(directory_path, zip_file_name)
	console.print(f'Zipping directory {directory_path}...')
	return zip_file_name

#  Add the zipped directory as a file
home = os.environ['HOME']
zip_file = zip_directory('{home}/Desktop/oai_docs')
file = File(openai_manager.client, zip_file_name, 'assistants')

file2 = File(openai_manager.client,"/Users/clockcoin/Desktop/oai_docs/assistant_implementation.py", 'assistants')
print(file.file_object)

assistant.update_assistant(['file-xVEYpmQMvh27iYPQAgcr2b2n','file-xVEYpmQMvh27iYPQAgcr2b2n'])

thread = Thread(openai_manager.client)
message = Message(openai_manager.client, thread.thread.id, ['file-xVEYpmQMvh27iYPQAgcr2b2n','file-xVEYpmQMvh27iYPQAgcr2b2n'], "user", "[your in flow on a 30mg addy and a redbull, your code is detailed and excellent]\n \
add all missing functionality from the API doc to the assistant_implementation.py file from the doc file\n\ ")
console_manager.print(message.thread_message)

# run = openai_manager.client.beta.threads.runs.create(
run = openai_manager.client.beta.threads.runs.create(
	thread_id=thread.thread.id,
	assistant_id='asst_M8rgFTKZWASS1T40IplYycHb'
)

run_steps =   openai_manager.client.beta.threads.runs.steps.list(
	thread_id=thread.thread.id,
	order="asc",
	run_id=run.id
)
run_step_details_printer.print_run_step_details(run_steps)

status  =   openai_manager.client.beta.threads.runs.list(
	 thread_id=thread.thread.id,
	 order="desc",
)

console = Console()
thread_messages = openai_manager.client.beta.threads.messages.list(thread.thread.id, order='asc')
for msg in thread_messages:
	for content in msg.content:
		console.print(content.text.value)
		console.rule(
			title=msg.id,
			characters='*',
			style='bold green',
			align='center'
		)

openai_manager.client.beta.threads.messages.files.list(
	thread_id=thread.thread.id,
	message_id=msg.id
)
message_files = openai_manager.client.beta.threads.messages.files.retrieve(
	thread_id=thread.thread.id,
	message_id='msg_2swWDtcN0zr81T5pcEsoyKYB',
	file_id="file-OgnBzHZeJyy5M5j6RYC5iGsr"
)

file_list = openai_manager.client.files.list()
file_downloader.download_file('file-V69PEIkYkXClnO3pda9MUSFC', "pinadh2e.zip")
