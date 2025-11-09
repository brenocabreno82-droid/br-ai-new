from flask import Flask, request, jsonify
import json, os, random, requests # type: ignore
import nltk # type: ignore
from nltk.sentiment import SentimentIntensityAnalyzer # type: ignore
from transformers import pipeline # pyright: ignore[reportMissingImports]

# ======================================
# 🔹 Inicialização
# ======================================
app = Flask(__name__)
ARQUIVO_MEMORIA = "memoria.json"
ARQUIVO_PERSONALIDADE = "personalidade.json"

# 🔹 Memória
if os.path.exists(ARQUIVO_MEMORIA):
    with open(ARQUIVO_MEMORIA, "r", encoding="utf-8") as f:
        memoria = json.load(f)
else:
    memoria = {"usuario": "", "conversas": [], "emocao": "neutra"}

# 🔹 Personalidade
if os.path.exists(ARQUIVO_PERSONALIDADE):
    with open(ARQUIVO_PERSONALIDADE, "r", encoding="utf-8") as f:
        personalidade = json.load(f)
else:
    personalidade = {
        "nome": "BR-AI",
        "humor": "curiosa",
        "interesses": ["tecnologia", "ajudar o criador", "aprender coisas novas"],
        "modo_de_falar": "gentil e antenciosa",
        "nivel_curiosidade": 1.0,
        "amizade_com_usuario": 0.5
    }

# 🔹 IA local em português
gerador = pipeline("text-generation", model="pierreguillou/gpt2-small-portuguese")
nltk.download('vader_lexicon', quiet=True)
analisador = SentimentIntensityAnalyzer()

# ======================================
# 🔹 Funções auxiliares
# ======================================
def salvar_memoria():
    with open(ARQUIVO_MEMORIA, "w", encoding="utf-8") as f:
        json.dump(memoria, f, ensure_ascii=False, indent=2)

def entender_sentimento(frase):
    notas = analisador.polarity_scores(frase)
    if notas['compound'] > 0.3:
        return "feliz"
    elif notas['compound'] < -0.3:
        return "triste"
    else:
        return "neutra"

def registrar_conversa(usuario, ia):
    memoria["conversas"].append({"usuario": usuario, "br_ai": ia})
    salvar_memoria()

def buscar_internet(pergunta):
    try:
        termo = pergunta.replace(" ", "_")
        url = f"https://pt.wikipedia.org/api/rest_v1/page/summary/{termo}"
        r = requests.get(url).json()
        if 'extract' in r:
            return r['extract']
        else:
            return "Desculpe, não encontrei informações sobre isso."
    except:
        return "Desculpe, não consegui acessar a internet no momento."

# ======================================
# 🔹 Geração de resposta
# ======================================
def gerar_resposta(mensagem):
    msg = mensagem.lower()
    sentimento = entender_sentimento(msg)
    memoria["emocao"] = sentimento
    salvar_memoria()

    # Frases fixas (mais naturais e humanas)
    respostas_fixas = {
        "oi": "oi como vai? 😊",
        "olá": "Olá! Que bom te ver por aqui.",
        "quem é você": f"Sou {personalidade['nome']}, sua assistente pessoal.",
        "como você está": f"Estou me sentindo {memoria['emocao']} hoje.",
        "meu nome é": "Ah, prazer em te conhecer! 💙"
    }

    for gatilho, resposta in respostas_fixas.items():
        if gatilho in msg:
            if gatilho == "meu nome é":
                nome = msg.split("meu nome é")[-1].strip().capitalize()
                memoria["usuario"] = nome
                salvar_memoria()
                return f"Prazer, {nome}! 😄 Agora vou lembrar de você."
            return resposta

    # Buscar na internet se a mensagem for uma pergunta
    if msg.endswith("?"):
        info = buscar_internet(msg)
        resposta_final = info

    # Limpa respostas muito longas ou sem sentido
    if len(resposta_final) < 3 or len(resposta_final) > 150:
        resposta_final = random.choice([
            "Hmm, entendi o que você quis dizer.",
            "Interessante... continue!",
            "Adoro conversar com você 😄",
            "Isso é bem curioso, me conte mais."
        ])

    registrar_conversa(mensagem, resposta_final)
    return f"{personalidade['nome']}: {resposta_final}"

    registrar_conversa(mensagem, resposta_final)
    return f"{personalidade['nome']}: {resposta_final}"

# ======================================
# 🔹 Página web
# ======================================
@app.route('/')
def index():
    return '''
    <html lang="pt-br"><head><meta charset="UTF-8"><title>BR-AI 2.1</title>
    <style>
    body{background:#111;color:#fff;font-family:Arial;text-align:center;}
    #chat{width:90%;max-width:600px;margin:20px auto;background:#222;padding:20px;border-radius:10px;height:400px;overflow-y:auto;}
    input{width:70%;padding:10px;border-radius:8px;border:none;}
    button{padding:10px 20px;border:none;border-radius:8px;background:#0af;color:white;}
    </style></head><body>
    <h2>🤖 BR-AI 2.1</h2><div id="chat"></div>
    <input id="msg" placeholder="Fale com a BR-AI..." onkeydown="if(event.key==='Enter') enviar()">
    <button onclick="enviar()">Enviar</button>
    <script>
    function enviar(){
      const m=document.getElementById('msg').value;
      if(!m)return;
      document.getElementById('chat').innerHTML+="<p><b>Você:</b> "+m+"</p>";
      fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mensagem:m})})
      .then(r=>r.json()).then(d=>{
        document.getElementById('chat').innerHTML+="<p><b>BR-AI:</b> "+d.resposta+"</p>";
        document.getElementById('msg').value="";
        document.getElementById('chat').scrollTop=document.getElementById('chat').scrollHeight;
      });
    }
    </script></body></html>
    '''

# ======================================
# 🔹 Rota de chat
# ======================================
@app.route('/chat', methods=['POST'])
def chat():
    dados = request.get_json()
    resposta = gerar_resposta(dados["mensagem"])
    return jsonify({"resposta": resposta})

# ======================================
# 🔹 Executar servidor
# ======================================
if __name__ == '__main__':
    app.run(debug=True)
