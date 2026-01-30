# Chatbots

A small command-line chatbot that sends your prompts to an LLM via the OpenAI API. You type a multiline prompt in the terminal, submit with **Ctrl-S** or abort with **Ctrl-C**. The program reports how long the request took and how many tokens were used, then prints the model’s reply. A system prompt (e.g. “You are a helpful math assistant”) is read from `prompts.txt` in the project directory so you can customize the assistant’s behavior.
