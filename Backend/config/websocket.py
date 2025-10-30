"""
A simple websocket application that handles ping/pong messages.

This application demonstrates how to write a basic websocket application
using the ASGI interface. It accepts a websocket connection, responds to
ping messages with pong messages, and terminates the connection when the
client disconnects.

"""


async def websocket_application(scope, receive, send):
    """
    Handle a websocket connection.

    This function will be called whenever a new websocket connection is
    established. It will receive messages from the client and send messages
    back.

    Args:
        scope (dict): The scope of the connection. This is a dictionary that
            contains information about the connection, such as the path and
            headers.
        receive (async function): An async function that can be used to receive
            messages from the client.
        send (async function): An async function that can be used to send
          messages
            back to the client.
    """

    while True:
        event = await receive()

        if event["type"] == "websocket.connect":
            await send({"type": "websocket.accept"})

        if event["type"] == "websocket.disconnect":
            break

        if event["type"] == "websocket.receive":
            if event["text"] == "ping":
                await send({"type": "websocket.send", "text": "pong!"})
