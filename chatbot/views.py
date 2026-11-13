
import requests

from django.conf import settings
from django.shortcuts import render
from .models import Conversation, Message


def chat_home(request):

    # Get existing conversation from browser session
    conversation_id = request.session.get('conversation_id')

    conversation = None

    if conversation_id:
        conversation = Conversation.objects.filter(
            id=conversation_id
        ).first()

    # Create a conversation if one doesn't exist
    if conversation is None:
        conversation = Conversation.objects.create()
        request.session['conversation_id'] = conversation.id

    if request.method == "POST":

        question = request.POST.get("message", "").strip()

        if question:

            # Save user question
            Message.objects.create(
                conversation=conversation,
                role='user',
                content=question
            )

            try:

                # Retrieve previous conversation messages
                previous_messages = Message.objects.filter(
                    conversation=conversation
                ).order_by('created_at', 'id')[:20]

                messages = [
                    {
                        "role": "system",
                        "content": "You are AVL AI Assistant. Give helpful, clear and accurate answers."
                    }
                ]

                for msg in previous_messages:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })

                # Send conversation history to Ollama
                response = requests.post(
                    settings.OLLAMA_URL,
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "messages": messages,
                        "stream": False
                    },
                    timeout=180
                )

                response.raise_for_status()

                answer = response.json()["message"]["content"]

                # Save AI response
                Message.objects.create(
                    conversation=conversation,
                    role='assistant',
                    content=answer
                )

                # Set conversation title from first question
                if conversation.title == "New Chat":
                    conversation.title = question[:50]
                    conversation.save()

            except requests.exceptions.ConnectionError:
                answer = "Ollama is not running. Please start Ollama."

            except requests.exceptions.Timeout:
                answer = "AI response timed out. Please try again."

            except requests.exceptions.RequestException as e:
                answer = f"Ollama API error: {e}"

    messages = Message.objects.filter(
        conversation=conversation
    ).order_by('created_at', 'id')

    return render(
        request,
        "chatbot/index.html",
        {
            "messages": messages,
            "conversation": conversation
        }
    )
