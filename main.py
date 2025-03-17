from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
import os
import time
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

if not OPENAI_API_KEY or not ASSISTANT_ID:
    raise ValueError("As variáveis de ambiente OPENAI_API_KEY e OPENAI_ASSISTANT_ID precisam estar definidas!")

openai.api_key = OPENAI_API_KEY

# Estrutura esperada para mensagens recebidas
class MessageRequest(BaseModel):
    message: str
    thread_id: str | None = None  # Thread opcional para manter contexto

@app.post("/chat")
async def chat(request: MessageRequest):
    try:
        print(f"Recebendo mensagem: {request.message}")

        # Criar uma nova thread se não houver uma já existente
        if not request.thread_id:
            thread = openai.beta.threads.create()
            thread_id = thread.id
            print(f"Nova thread criada: {thread_id}")
        else:
            thread_id = request.thread_id

        # Adicionar mensagem à thread existente
        openai.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=request.message
        )

        print(f"Mensagem enviada à thread {thread_id}")

        # Criar uma execução para processar a resposta
        run = openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )

        print(f"Execução iniciada: {run.id}")

        # Esperar o processamento da resposta do assistente
        while True:
            run_status = openai.beta.threads.runs.retrieve(
                thread_id=thread_id, run_id=run.id
            )
            if run_status.status == "completed":
                break
            print("Aguardando resposta do assistente...")
            time.sleep(2)  # Pequena pausa para evitar excesso de requisições

        # Obter todas as mensagens da thread
        messages = openai.beta.threads.messages.list(thread_id=thread_id)

        # Pegar apenas a última resposta gerada pelo assistente
        response_text = None
        for msg in reversed(messages.data):  # Verifica da última para a primeira
            if msg.role == "assistant":
                response_text = msg.content[0].text.value
                break

        if not response_text:
            response_text = "Desculpe, não consegui processar a resposta."

        print(f"Resposta do assistente: {response_text}")

        return {"response": response_text, "thread_id": thread_id}

    except Exception as e:
        print(f"Erro no backend: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "API do Laudobot funcionando!"}
