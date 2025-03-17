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

class MessageRequest(BaseModel):
    message: str
    thread_id: str | None = None  # Permitir conversas contínuas

@app.post("/chat")
async def chat(request: MessageRequest):
    try:
        print(f"Recebendo mensagem: {request.message}")

        # Criar uma nova thread se não houver uma já existente
        if not request.thread_id:
            thread = openai.threads.create()
            thread_id = thread.id
            print(f"Nova thread criada: {thread_id}")
        else:
            thread_id = request.thread_id

        # Adicionar a mensagem do usuário à thread
        openai.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=request.message
        )

        print(f"Mensagem enviada à thread {thread_id}")

        # Criar uma execução do assistente na thread
        run = openai.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )

        print(f"Execução iniciada: {run.id}")

        # 🔥 **ESPERAR O PROCESSAMENTO DA RESPOSTA**
        while True:
            run_status = openai.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            print(f"Status da execução: {run_status.status}")
            if run_status.status == "completed":
                break
            time.sleep(3)

        # 🔥 **BUSCAR A ÚLTIMA RESPOSTA DO ASSISTENTE APÓS O PROCESSAMENTO**
        messages = openai.threads.messages.list(thread_id=thread_id)

        # Encontrar a última resposta do assistente
        response_text = None
        for msg in reversed(messages.data):
            if msg.role == "assistant" and msg.content:
                response_text = msg.content[0].text.value
                break

        if not response_text:
            response_text = "Desculpe, não consegui processar a resposta corretamente."

        print(f"Resposta do assistente: {response_text}")

        return {"response": response_text, "thread_id": thread_id}

    except Exception as e:
        print(f"Erro no backend: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "API do Laudobot funcionando!"}
