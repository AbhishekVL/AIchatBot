
import requests

from django.conf import settings
from django.shortcuts import render


def chat_home(request):
    answer = ""
    question = ""

    if request.method == "POST":

        question = request.POST.get("message", "").strip()

        if question:
            try:
                response = requests.post(
                    settings.OLLAMA_URL,
                    json={
                        "model": settings.OLLAMA_MODEL,
                        "messages": [
                            {
                                "role": "user",
                                "content": question
                            }
                        ],
                        "stream": False
                    },
                    timeout=120
                )

                response.raise_for_status()

                data = response.json()

                answer = data["message"]["content"]

            except requests.exceptions.ConnectionError:
                answer = "Ollama is not running. Please start Ollama."

            except requests.exceptions.Timeout:
                answer = "AI is taking too long to respond. Please try again."

            except requests.exceptions.RequestException as e:
                answer = f"Ollama API error: {e}"

            except Exception as e:
                answer = f"Something went wrong: {e}"

    return render(
        request,
        "chatbot/index.html",
        {
            "answer": answer,
            "question": question
        }
    )
