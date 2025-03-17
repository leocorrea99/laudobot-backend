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

@app.post("/chat")
async def chat(request: MessageRequest):
    try:
        print(f"Recebendo mensagem: {request.message}")  # Log da mensagem recebida

        # Criar uma nova thread para a conversa
        thread = openai.beta.threads.create()
        thread_id = thread.id  

        print(f"Thread criada: {thread_id}")  # Log da criação da thread

        # Enviar a mensagem do usuário para a thread
        openai.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=request.message
        )

        print("Mensagem enviada ao assistente")  # Log da mensagem enviada

        # Criar a execução do assistente
        run = openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID
        )

        print(f"Execução iniciada: {run.id}")  # Log da execução do assistente

        # Aguardar o processamento da resposta
        while True:
            run_status = openai.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
            if run_status.status == "completed":
                break
            print("Aguardando resposta do assistente...")
            time.sleep(2)  # Pequena pausa para evitar excesso de requisições

        # Obter a resposta gerada pelo assistente
        messages = openai.beta.threads.messages.list(thread_id=thread_id)
        response_text = messages.data[-1].content[0].text.value  # Pegando a última resposta

        print(f"Resposta do assistente: {response_text}")  # Log da resposta do assistente

        return {"response": response_text}

    except Exception as e:
        print(f"Erro no backend: {str(e)}")  # Log do erro nos logs da Render
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "API do Laudobot funcionando!"}

