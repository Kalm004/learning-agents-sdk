from agents import Agent, Runner, WebSearchTool, trace
from dotenv import load_dotenv
from agents.mcp import MCPServer, MCPServerStdio
import asyncio
import os
load_dotenv()

async def run(server: MCPServer, query: str):
    web_search_agent = Agent(
        name="Web Search Agent",
        model="gpt-4.1-mini",
        instructions="You provide assistance with web search queries. Search the web for information and return the results.",
        tools= [WebSearchTool()]
    )

    onenote_agent = Agent(
        name="OneNote Agent",
        model="gpt-4.1-mini",
        instructions="Don't relly on your own knowledge. You provide assistance with one note queries. You can find the notes in OneNote and get the content of the notes to answer the user's question.",
        mcp_servers=[server]
    )

    orchestrator_agent = Agent(
        name="Orchestrator Agent",
        model="gpt-4.1-mini",
        instructions="You are a helpful assistant. Don't relly on your own knowledge. Your job is assisting me on finding information I've already written down in OneNote or extending that information with information you find on the web. You orchestrate the one note agent and the web search agent to find the information you need. You are the final agent in the chain of agents. You return the final output of the one note agent and the web search agent.",
        tools= [
            web_search_agent.as_tool(
                tool_name="web_search_agent",
                tool_description="Search the web for information",
            ),
            onenote_agent.as_tool(
                tool_name="onenote_agent",
                tool_description="Find the information in OneNote",
            )],
    )
    conversation_history = []
    while True:
        query = input("Enter your question: ")
        if query == "exit":
            break
        conversation_history.append({"role": "user", "content": query})
        result = await Runner.run(orchestrator_agent, conversation_history)
        print(result.final_output)
        conversation_history.append({"role": "assistant", "content": result.final_output})

async def main():
    async with MCPServerStdio(
        name="OneNote MCP Server",
        params={
            "command": os.getenv("ONENOTE_MCP_PYTHON_PATH"),
            "args": [os.getenv("ONENOTE_MCP_SCRIPT_PATH")],
            "description": "OneNote MCP Server",
            "timeout": 60,
        },
    ) as server:
        with trace(workflow_name="OneNote MCP Server"):
            await run(server, "What is written in my notes about LoRA in AI?")

if __name__ == "__main__":
    asyncio.run(main())