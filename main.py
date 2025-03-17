from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
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
    message: str = Field(..., example="Olá, tudo bem?")
    thread_id: str | None = Field(None, example="thread_xxxxx")

@app.post("/chat")
async def chat(request: MessageRequest):
    try:
        print(f"Recebendo mensagem: {request.message}")  # Log da mensagem recebida

        # Se não houver uma thread, criamos uma nova
        if not request.thread_id:
            thread = openai.beta.threads.create()
            thread_id = thread.id
            print(f"Nova thread criada: {thread_id}")  # Log da criação da thread
        else:
            thread_id = request.thread_id

        # Enviar a mensagem do usuário para a thread
        openai.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=request.message
        )

        print("Mensagem enviada ao assistente")  # Log da mensagem enviada

        # Criar a execução do assistente **usando o Assistant ID correto**
        run = openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=ASSISTANT_ID,
            instructions="Siga as diretrizes do assistente configurado no Playground."
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
        
        # Verificar se há uma resposta válida
        if messages.data:
            response_text = messages.data[-1].content[0].text.value  # Pegando a última resposta gerada
            print(f"Resposta do assistente: {response_text}")  # Log da resposta
        else:
            response_text = "Desculpe, não consegui processar a resposta."
            print("Erro: O assistente não gerou uma resposta válida.")

        return {"response": response_text, "thread_id": thread_id}  # Retorna o thread_id para manter a conversa

    except Exception as e:
        print(f"Erro no backend: {str(e)}")  # Log do erro nos logs da Render
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "API do Laudobot funcionando!"}
