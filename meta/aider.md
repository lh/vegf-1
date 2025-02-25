
## Aider commands

/add            Add files to the chat so aider can edit them or review them in detail
/architect      Enter architect/editor mode using 2 different models. If no prompt provided,
switches to architect/editor mode.
/ask            Ask questions about the code base without editing any files. If no prompt 
provided, switches to ask mode.
/chat-mode      Switch to a new chat mode
/clear          Clear the chat history
/code           Ask for changes to your code. If no prompt provided, switches to code mode.
/commit         Commit edits to the repo made outside the chat (commit message optional)
/copy           Copy the last assistant message to the clipboard
/copy-context   Copy the current chat context as markdown, suitable to paste into a web UI
/diff           Display the diff of changes since the last message
/drop           Remove files from the chat session to free up context space
/editor         Open an editor to write a prompt
/exit           Exit the application
/git            Run a git command (output excluded from chat)
/help           Ask questions about aider
/lint           Lint and fix in-chat files or all dirty files if none in chat
/load           Load and execute commands from a file/save s
/ls             List all known files and indicate which are included in the chat session
/map            Print out the current repository map
/map-refresh    Force a refresh of the repository map
/model          Switch to a new LLM
/models         Search the list of available models
/multiline-mode Toggle multiline mode (swaps behavior of Enter and Meta+Enter)
/paste          Paste image/text from the clipboard into the chat.        Optionally provide
a name for the image.
/quit           Exit the application
/read-only      Add files to the chat that are for reference only, or turn added files to 
read-only
/report         Report a problem by opening a GitHub Issue
/reset          Drop all files and clear the chat history
/run            Run a shell command and optionally add the output to the chat (alias: !)
/save           Save commands to a file that can reconstruct the current chat session's 
files
/settings       Print out the current settings
/test           Run a shell command and add the output to the chat on non-zero exit code
/tokens         Report on the number of tokens used by the current chat context
/undo           Undo the last git commit if it was done by aider
/voice          Record and transcribe voice input
/web            Scrape a webpage, convert to markdown and send in a message