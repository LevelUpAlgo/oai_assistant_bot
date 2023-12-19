`OpenAI Assistants API Docs Beta`
The Assistants API allows you to build AI assistants within your own applications. An Assistant has instructions and can leverage models, tools, and knowledge to respond to user queries. The Assistants API currently supports three types of tools: Code Interpreter, Retrieval, and Function calling. In the future, we plan to release more OpenAI-built tools, and allow you to provide your own tools on our platform.

You can explore the capabilities of the Assistants API using the Assistants playground or by building a step-by-step integration outlined in this guide. At a high level, a typical integration of the Assistants API has the following flow:

- Create an Assistant in the API by defining its custom instructions and picking a model. If helpful, enable tools like Code Interpreter, Retrieval, and Function calling.
- Create a Thread when a user starts a conversation.
- Add Messages to the Thread as the user ask questions.
- Run the Assistant on the Thread to trigger responses. This automatically calls the relevant tools.
- Calls to the Assistants API require that you pass a beta HTTP header. This is handled automatically if you’re using OpenAI’s official Python or Node.js SDKs.
- OpenAI-Beta: assistants=v1

`This starter guide walks through the key steps to create and run an Assistant that uses Code Interpreter`

**Step 1: Create an Assistant**
An Assistant represents an entity that can be configured to respond to users’ Messages using several parameters like:
```
Instructions: how the Assistant and model should behave or respond
Model: you can specify any GPT-3.5 or GPT-4 models, including fine-tuned models. The Retrieval tool requires gpt-3.5-turbo-1106 and gpt-4-1106-preview models.
Tools: the API supports Code Interpreter and Retrieval that are built and hosted by OpenAI.
Functions: the API allows you to define custom function signatures, with similar behavior as our function calling feature.
In this example, we're [creating an Assistant[(/docs/api-reference/assistants/createAssistant)] that is a personal math tutor, with the Code Interpreter tool enabled.
```
```python
assistant = client.beta.assistants.create(
    name="Math Tutor",
    instructions="You are a personal math tutor. Write and run code to answer math questions.",
    tools=[{"type": "code_interpreter"}],
    model="gpt-4-1106-preview"
)
```
**Step 2: Create a Thread**
A Thread represents a conversation. We recommend creating one Thread per user as soon as the user initiates the conversation. Pass any user-specific context and files in this thread by creating Messages.
```python
thread = client.beta.threads.create()
```
Threads don’t have a size limit. You can add as many Messages as you want to a Thread. The Assistant will ensure that requests to the model fit within the maximum context window, using relevant optimization techniques such as truncation which we have tested extensively with ChatGPT. When you use the Assistants API, you delegate control over how many input tokens are passed to the model for any given Run, this means you have less control over the cost of running your Assistant in some cases but do not have to deal with the complexity of managing the context window yourself.

**Step 3: Add a Message to a Thread**
A Message contains text, and optionally any files that you allow the user to upload. Messages need to be added to a specific Thread. Adding images via message objects like in Chat Completions using GPT-4 with Vision is not supported today, but we plan to add support for them in the coming months. You can still upload images and have them processes via retrieval.
```python
message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content="I need to solve the equation `3x + 11 = 14`. Can you help me?"
)
```
Now if you list the Messages in a Thread, you will see that this message has been appended.
```python
{
  "object": "list",
  "data": [
    {
      "created_at": 1696995451,
      "id": "msg_abc123",
      "object": "thread.message",
      "thread_id": "thread_abc123",
      "role": "user",
      "content": [{
        "type": "text",
        "text": {
          "value": "I need to solve the equation `3x + 11 = 14`. Can you help me?",
          "annotations": []
        }
          }],
        ...
```
**Step 4: Run the Assistant**
For the Assistant to respond to the user message, you need to create a Run. This makes the Assistant read the Thread and decide whether to call tools (if they are enabled) or simply use the model to best answer the query. As the run progresses, the assistant appends Messages to the thread with the role="assistant". The Assistant will also automatically decide what previous Messages to include in the context window for the model. This has both an impact on pricing as well as model performance. The current approach has been optimized based on what we learned building ChatGPT and will likely evolve over time.
You can optionally pass additional instructions to the Assistant while creating the Run but note that these instructions override the default instructions of the Assistant.
```python
run = client.beta.threads.runs.create(
  thread_id=thread.id,
  assistant_id=assistant.id,
  instructions="Please address the user as Jane Doe. The user has a premium account."
)
```
**Step 5: Check the Run status**
By default, a Run goes into the queued state. You can periodically retrieve the Run to check on its status to see if it has moved to completed.
```python
run = client.beta.threads.runs.retrieve(
  thread_id=thread.id,
  run_id=run.id
)
```
**Step 6: Display the Assistant's Response**
Once the Run completes, you can list the Messages added to the Thread by the Assistant.
```python
messages = client.beta.threads.messages.list(
  thread_id=thread.id
)
```
And finally, display them to the user! During this Run, the Assistant added two new Messages to the Thread. Here is an example of what that might look like:

`ROLE	CONTENT`
user:	I need to solve the equation 3x + 11 = 14. Can you help me?
assistant: Certainly, Jane Doe. To solve the equation (3x + 11 = 14) for (x), you'll want to isolate (x) on one side of the equation. Here's how you can do that:
Subtract 11 from both sides of the equation to get (3x = 3).
Then, divide both sides by 3 to solve for (x).
Let me calculate the value of (x) for you.
assistant	The solution to the equation (3x + 11 = 14) is (x = 1).
You can also retrieve the Run Steps of this Run if you'd like to explore or display the inner workings of the Assistant and its tools.
-------------------------

`Tools Beta`
Give Assistants access to OpenAI-hosted tools like Code Interpreter and Knowledge Retrieval, or build your own tools using Function calling. Usage of OpenAI-hosted tools comes at an additional fee — visit our help center article to learn more about how these tools are priced.

The Assistants API is in beta and we are actively working on adding more functionality. Share your feedback in our Developer Forum!
`Code Interpreter`
Code Interpreter allows the Assistants API to write and run Python code in a sandboxed execution environment. This tool can process files with diverse data and formatting, and generate files with data and images of graphs. Code Interpreter allows your Assistant to run code iteratively to solve challenging code and math problems. When your Assistant writes code that fails to run, it can iterate on this code by attempting to run different code until the code execution succeeds.

*Enabling Code Interpreter*
Pass the code_interpreterin the tools parameter of the Assistant object to enable Code Interpreter:
```python
assistant = client.beta.assistants.create(
  instructions="You are a personal math tutor. When asked a math question, write and run code to answer the question.",
  model="gpt-4-1106-preview",
  tools=[{"type": "code_interpreter"}]
)
```
The model then decides when to invoke Code Interpreter in a Run based on the nature of the user request. This behavior can be promoted by prompting in the Assistant's instructions (e.g., “write code to solve this problem”).

*Passing files to Code Interpreter*
Code Interpreter can parse data from files. This is useful when you want to provide a large volume of data to the Assistant or allow your users to upload their own files for analysis.

Files that are passed at the Assistant level are accessible by all Runs with this Assistant:
```python
# Upload a file with an "assistants" purpose
file = client.files.create(
  file=open("speech.py", "rb"),
  purpose='assistants'
)

# Create an assistant using the file ID
assistant = client.beta.assistants.create(
  instructions="You are a personal math tutor. When asked a math question, write and run code to answer the question.",
  model="gpt-4-1106-preview",
  tools=[{"type": "code_interpreter"}],
  file_ids=[file.id]
)
```
Files can also be passed at the Thread level. These files are only accessible in the specific Thread. Upload the File using the File upload endpoint and then pass the File ID as part of the Message creation request:

```python
thread = client.beta.threads.create(
  messages=[
    {
      "role": "user",
      "content": "I need to solve the equation `3x + 11 = 14`. Can you help me?",
      "file_ids": [file.id]
    }
  ]
)
```
Files have a maximum size of 512 MB. Code Interpreter supports a variety of file formats including .csv, .pdf, .json and many more. More details on the file extensions (and their corresponding MIME-types) supported can be found in the Supported files section below.

`Reading images and files generated by Code Interpreter`
Code Interpreter in the API also outputs files, such as generating image diagrams, CSVs, and PDFs. There are two types of files that are generated:

`Images`
Data files (e.g. a csv file with data generated by the Assistant)
When Code Interpreter generates an image, you can look up and download this file in the file_id field of the Assistant Message response:
```python
{
    "id": "msg_abc123",
    "object": "thread.message",
    "created_at": 1698964262,
    "thread_id": "thread_abc123",
    "role": "assistant",
    "content": [
    {
      "type": "image_file",
      "image_file": {
        "file_id": "file-abc123"
      }
    }
  ]
  # ...
}
```
The file content can then be downloaded by passing the file ID to the Files API:
```python
from openai import OpenAI

client = OpenAI()

image_data = client.files.content("file-abc123")
image_data_bytes = image_data.read()

with open("./my-image.png", "wb") as file:
    file.write(image_data_bytes)
When Code Interpreter references a file path (e.g., ”Download this csv file”), file paths are listed as annotations. You can convert these annotations into links to download the file:

{
  "id": "msg_abc123",
  "object": "thread.message",
  "created_at": 1699073585,
  "thread_id": "thread_abc123",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": {
        "value": "The rows of the CSV file have been shuffled and saved to a new CSV file. You can download the shuffled CSV file from the following link:\n\n[Download Shuffled CSV File](sandbox:/mnt/data/shuffled_file.csv)",
        "annotations": [
          {
            "type": "file_path",
            "text": "sandbox:/mnt/data/shuffled_file.csv",
            "start_index": 167,
            "end_index": 202,
            "file_path": {
              "file_id": "file-abc123"
            }
          }
          ...
```
`Input and output logs of Code Interpreter`
By listing the steps of a Run that called Code Interpreter, you can inspect the code input and outputs logs of Code Interpreter:
```python
run_steps = client.beta.threads.runs.steps.list(
  thread_id=thread.id,
  run_id=run.id
)
{
  "object": "list",
  "data": [
    {
      "id": "step_abc123",
      "object": "thread.run.step",
      "type": "tool_calls",
      "run_id": "run_abc123",
      "thread_id": "thread_abc123",
      "status": "completed",
      "step_details": {
        "type": "tool_calls",
        "tool_calls": [
          {
            "type": "code",
            "code": {
              "input": "# Calculating 2 + 2\nresult = 2 + 2\nresult",
              "outputs": [
                {
                  "type": "logs",
                  "logs": "4"
                }
                        ...
 }
```
`Knowledge Retrieval`
Retrieval augments the Assistant with knowledge from outside its model, such as proprietary product information or documents provided by your users. Once a file is uploaded and passed to the Assistant, OpenAI will automatically chunk your documents, index and store the embeddings, and implement vector search to retrieve relevant content to answer user queries.

*Enabling Retrieval*
Pass the retrieval in the tools parameter of the Assistant to enable Retrieval:
```python
assistant = client.beta.assistants.create(
  instructions="You are a customer support chatbot. Use your knowledge base to best respond to customer queries.",
  model="gpt-4-1106-preview",
  tools=[{"type": "retrieval"}]
)
```

`How it works`
The model then decides when to retrieve content based on the user Messages. The Assistants API automatically chooses between two retrieval techniques:
it either:
- passes the file content in the prompt for short documents
or
- performs a vector search for longer documents
Retrieval currently optimizes for quality by adding all relevant content to the context of model calls. We plan to introduce other retrieval strategies to enable developers to choose a different tradeoff between retrieval quality and model usage cost.

`Uploading files for retrieval`
Similar to Code Interpreter, files can be passed at the Assistant-level or at the Thread-level
```python
# Upload a file with an "assistants" purpose
file = client.files.create(
  file=open("knowledge.pdf", "rb"),
  purpose='assistants'
)

# Add the file to the assistant
assistant = client.beta.assistants.create(
  instructions="You are a customer support chatbot. Use your knowledge base to best respond to customer queries.",
  model="gpt-4-1106-preview",
  tools=[{"type": "retrieval"}],
  file_ids=[file.id]
)
```
Files can also be added to a Message in a Thread. These files are only accessible within this specific thread. After having uploaded a file, you can pass the ID of this File when creating the Message:
```python
message = client.beta.threads.messages.create(
  thread_id=thread.id,
  role="user",
  content="I can not find in the PDF manual how to turn off this device.",
  file_ids=[file.id]
)
```
Maximum file size is 512MB. Retrieval supports a variety of file formats including .pdf, .md, .docx and many more. More details on the file extensions (and their corresponding MIME-types) supported can be found in the Supported files section below.

`Deleting files`
To remove a file from the assistant, you can detach the file from the assistant:
```python
file_deletion_status = client.beta.assistants.files.delete(
  assistant_id=assistant.id,
  file_id=file.id
)
```
Detaching the file from the assistant removes the file from the retrieval index as well.

`File citations`
When Code Interpreter outputs file paths in a Message, you can convert them to corresponding file downloads using the annotations field. See the Annotations section for an example of how to do this.
```python
{
    "id": "msg_abc123",
    "object": "thread.message",
    "created_at": 1699073585,
    "thread_id": "thread_abc123",
    "role": "assistant",
    "content": [
      {
        "type": "text",
        "text": {
          "value": "The rows of the CSV file have been shuffled and saved to a new CSV file. You can download the shuffled CSV file from the following link:\n\n[Download Shuffled CSV File](sandbox:/mnt/data/shuffled_file.csv)",
          "annotations": [
            {
              "type": "file_path",
              "text": "sandbox:/mnt/data/shuffled_file.csv",
              "start_index": 167,
              "end_index": 202,
              "file_path": {
                "file_id": "file-abc123"
              }
            }
          ]
        }
      }
    ],
    "file_ids": [
      "file-abc456"
    ],
        ...
  },
```
`Function calling`
Similar to the Chat Completions API, the Assistants API supports function calling. Function calling allows you to describe functions to the Assistants and have it intelligently return the functions that need to be called along with their arguments. The Assistants API will pause execution during a Run when it invokes functions, and you can supply the results of the function call back to continue the Run execution.

`Defining functions`
First, define your functions when creating an Assistant:
```python
assistant = client.beta.assistants.create(
  instructions="You are a weather bot. Use the provided functions to answer questions.",
  model="gpt-4-1106-preview",
  tools=[{
      "type": "function",
    "function": {
      "name": "getCurrentWeather",
      "description": "Get the weather in location",
      "parameters": {
        "type": "object",
        "properties": {
          "location": {"type": "string", "description": "The city and state e.g. San Francisco, CA"},
          "unit": {"type": "string", "enum": ["c", "f"]}
        },
        "required": ["location"]
      }
    }
  }, {
    "type": "function",
    "function": {
      "name": "getNickname",
      "description": "Get the nickname of a city",
      "parameters": {
        "type": "object",
        "properties": {
          "location": {"type": "string", "description": "The city and state e.g. San Francisco, CA"},
        },
        "required": ["location"]
      }
    } 
  }]
)
```

`Reading the functions called by the Assistant`
When you initiate a Run with a user Message that triggers the function, the Run will enter a pending status. After it processes, the run will enter a requires_action state which you can verify by retrieving the Run. The model can provide multiple functions to call at once using parallel function calling:
```python
{
  "id": "run_abc123",
  "object": "thread.run",
  "assistant_id": "asst_abc123",
  "thread_id": "thread_abc123",
  "status": "requires_action",
  "required_action": {
    "type": "submit_tool_outputs",
    "submit_tool_outputs": {
      "tool_calls": [
        {
          "id": "call_abc123",
          "type": "function",
          "function": {
            "name": "getCurrentWeather",
            "arguments": "{\"location\":\"San Francisco\"}"
          }
        },
        {
          "id": "call_abc456",
          "type": "function",
          "function": {
            "name": "getNickname",
            "arguments": "{\"location\":\"Los Angeles\"}"
          }
        }
      ]
    }
  },
...
```

`Submitting functions outputs`
You can then complete the Run by submitting the tool output from the function(s) you call. Pass the tool_call_id referenced in the required_action object above to match output to each function call.
```python
run = client.beta.threads.runs.submit_tool_outputs(
  thread_id=thread.id,
  run_id=run.id,
  tool_outputs=[
      {
        "tool_call_id": call_ids[0],
        "output": "22C",
      },
      {
        "tool_call_id": call_ids[1],
        "output": "LA",
      },
    ]
)
```
After submitting outputs, the run will enter the queued state before it continues it’s execution.

**Supported files**
For text/ MIME types, the encoding must be one of utf-8, utf-16, or ascii.
FILE FORMAT	MIME TYPE Enabled for:	
CODE INTERPRETER, RETRIEVAL:
```md
.c	text/x-c		
.cpp	text/x-c++		
.csv	application/csv		
.docx	application/vnd.openxmlformats-officedocument.wordprocessingml.document		
.html	text/html		
.java	text/x-java		
.json	application/json		
.md	text/markdown		
.pdf	application/pdf		
.php	text/x-php		
.pptx	application/vnd.openxmlformats-officedocument.presentationml.presentation		
.py	text/x-python		
.py	text/x-script.python		
.rb	text/x-ruby		
.tex	text/x-tex		
.txt	text/plain
```

**FILE FORMAT	MIME TYPE ONLY Enabled for CODE INTERPRETER:**
```md
.jpeg	image/jpeg		
.jpg	image/jpeg		
.js	text/javascript		
.gif	image/gif		
.png	image/png		
.tar	application/x-tar		
.ts	application/typescript		
.xlsx	application/vnd.openxmlformats-officedocument.spreadsheetml.sheet		
.xml	application/xml or "text/xml"		
.zip	application/zip
```