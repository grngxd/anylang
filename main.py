import os
import platform

from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentConfig, HttpOptions

prompt = """
Convert the following code to LLVM IR.

Rules:
- Output only raw LLVM IR, no comments or code blocks.
- Do not include 'datalayout' or 'target triple'.
- For the most part, do not take the user's syntax literally, for example if they write
    `print "hello world"`, you should try convert it to a call to `puts` with the string constant.
- For every string constant:
  * The array size must be (string length + 1) for the null terminator (\00).
  * Make sure the size is not bigger or smaller than the length of the string
  * The string literal must end with \00 (single backslash, not double).
  * The type in getelementptr must exactly match the string constant's type.]

Example:

Anylang code:
print "whats good bro yooooo!"

LLVM IR:
@.str = private unnamed_addr constant [24 x i8] c"whats good bro yooooo!\00", align 1
declare i32 @puts(i8*)
define i32 @main() {
entry:
    %0 = call i32 @puts(i8* getelementptr inbounds ([24 x i8], [24 x i8]* @.str, i32 0, i32 0))
    ret i32 0
}
"""

load_dotenv()
api_key = os.getenv("API_KEY")
if not api_key:
    raise ValueError("API_KEY environment variable is not set.")

files = []
for root, dirs, filenames in os.walk(os.getcwd()):
    for filename in filenames:
        if filename.endswith(".any"):
            files.append(os.path.join(root, filename))

data = []
for file in files:
    with open(file, "r") as f:
        data.append(f.read())

print("Thinking...", end="", flush=True)

client = genai.Client(http_options=HttpOptions(api_version="v1"), vertexai=True, api_key=api_key)
response_stream = client.models.generate_content_stream(
    model="gemini-2.5-pro",
    contents=[
        "\n\n".join([f"# {os.path.basename(files[i])}\n{data[i]}" for i in range(len(files))]),
    ],
    config=GenerateContentConfig(
        temperature=0.05,
        system_instruction=prompt
    )
)

print("\rWriting...      ", end="", flush=True)

with open("out.ll", "w") as f:
    for chunk in response_stream:
        f.write(str(chunk.text))

print("\r" + " " * 40, end="\r", flush=True)

os.system("llc out.ll -o out.s")
if platform.system() == "Windows":
    os.system("clang out.s -o out.exe -O3")
else:
    os.system("clang out.s -o out -O3")


if platform.system() == "Windows":
    exit_code = os.system(".\\out.exe")
else:
    exit_code = os.system("./out")

print(f"anylang exited with code {exit_code}")