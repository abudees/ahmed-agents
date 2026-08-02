from anthropic import Anthropic

client = Anthropic()

def run_agent():
    """Simple agent that talks to Claude"""
    user_input = input("You: ")
    
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": user_input
            }
        ]
    )
    
    response = message.content[0].text
    print(f"\nAgent: {response}\n")

if __name__ == "__main__":
    print("Agent #1: Hello World Agent")
    print("Type 'quit' to exit\n")
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() == 'quit':
                break
            
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": user_input
                    }
                ]
            )
            
            response = message.content[0].text
            print(f"Agent: {response}\n")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break