# 📈 B3 Quote API

API REST em **Python + FastAPI** para consulta de cotações de ações da **B3 (Bovespa)** em tempo quase real, projetada para rodar **24/7** em uma máquina virtual da **Oracle Cloud Infrastructure (OCI)**.

## 🧱 Tecnologias

| Tecnologia | Função |
|---|---|
| Python 3.12 | Linguagem |
| FastAPI | Framework web (tipagem + Swagger/OpenAPI automático) |
| Uvicorn | Servidor ASGI de produção |
| yfinance | Fonte de dados (Yahoo Finance — tickers B3 com sufixo `.SA`) |
| Docker / Docker Compose | Deploy containerizado (Opção B) |
| systemd | Serviço em segundo plano com restart automático (Opção A) |

## 📂 Estrutura do repositório

```
b3-quote-api/
├── main.py             # Código-fonte da API
├── requirements.txt    # Dependências Python
├── Dockerfile          # Imagem Docker (multi-stage, produção)
├── docker-compose.yml  # Execução com um comando
├── api.service         # Unidade systemd (Opção A)
└── README.md           # Este arquivo
```

## 🔌 Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | Verifica se a API está online |
| GET | `/api/v1/quote/{ticker}` | Cotação atual (preço, variação, máx, mín, volume, timestamp) |
| GET | `/docs` | Swagger UI (documentação interativa) |
| GET | `/redoc` | Documentação alternativa (ReDoc) |

O ticker pode ser informado no formato B3 (`PETR4`, `VALE3`, `ITUB4`) — o sufixo `.SA` do Yahoo Finance é adicionado automaticamente.

**Códigos de erro tratados:** `422` formato de ticker inválido · `404` ticker inexistente · `502` falha na fonte de dados.

---

## 🗺️ Fluxo completo: do PC local até a VM (visão geral)

O caminho recomendado é: **testar tudo no seu PC → subir o código para o GitHub → clonar e rodar na VM → testar de fora**. Cada etapa aponta para a seção com os detalhes:

```
[Seu PC]                        [GitHub]              [VM Oracle Cloud]
   |                               |                         |
   | 1. Rodar e testar local       |                         |
   |    (seção 1)                  |                         |
   |------ git push -------------->|                         |
   |                               |------ git clone ------->|
   |                               |    2. Firewall (2.2)    |
   |                               |    3. Deploy A ou B     |
   |                               |       (2.3 ou 2.4)      |
   |<========== 4. Teste externo: curl / navegador =========|
```

**Etapa 1 — Testar no seu PC** *(seção 1)*: rode a API com `uvicorn` (e opcionalmente com Docker Desktop) e confirme que `http://localhost:8000/health` e `/api/v1/quote/PETR4` respondem. Só avance quando tudo funcionar localmente — depurar no PC é muito mais fácil que na VM.

**Etapa 2 — Subir para o GitHub**: crie um repositório vazio no GitHub (ex: `b3-quote-api`) e, na pasta do projeto no seu PC:

```bash
git init
git add main.py requirements.txt Dockerfile docker-compose.yml api.service README.md
git commit -m "Projeto B3 Quote API"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/b3-quote-api.git
git push -u origin main
```

**Etapa 3 — Preparar a VM**: libere a porta 8000 nas duas camadas de firewall *(seção 2.2)*.

**Etapa 4 — Deploy na VM**: conecte via SSH, clone o repositório e siga a **Opção A** (systemd, seção 2.3) ou a **Opção B** (Docker, seção 2.4).

**Etapa 5 — Testar de fora**: do seu PC (não da VM), rode `curl http://IP_PUBLICO_DA_VM:8000/health` e abra `http://IP_PUBLICO_DA_VM:8000/docs` no navegador *(seção 3)*. Se funcionar do seu PC, funciona de qualquer lugar — deploy concluído. ✅

**Para atualizar depois**: edite no PC → teste local → `git add . && git commit -m "ajuste" && git push` → na VM: `git pull` seguido de `sudo systemctl restart api` (Opção A) ou `docker compose up -d --build` (Opção B).

---

## 🖥️ 1. Rodando localmente (testes)

Pré-requisito: **Python 3.12+** instalado ([python.org/downloads](https://www.python.org/downloads/)).

> ⚠️ **Nota macOS/Homebrew:** Instale Python com `brew install python@3.12`. Ao usar Homebrew, o Python é "externally managed", então é **obrigatório** criar um ambiente virtual (venv) antes de instalar as dependências com `pip`.
>
> 💡 No Windows, durante a instalação do Python, marque a opção **"Add Python to PATH"**.

### 1.1 Linux

```bash
# 1. Clone o repositório
git clone https://github.com/SEU_USUARIO/b3-quote-api.git
cd b3-quote-api

# 2. Crie e ative o ambiente virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute a API
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 1.1b macOS (Homebrew)

```bash
# 1. Clone o repositório
git clone https://github.com/SEU_USUARIO/b3-quote-api.git
cd b3-quote-api

# 2. Instale Python 3.12 via Homebrew (se não estiver instalado)
brew install python@3.12

# 3. Crie e ative o ambiente virtual com Python 3.12
python3.12 -m venv venv
source venv/bin/activate

# 4. Atualize o pip e instale as dependências
pip install --upgrade pip
pip install -r requirements.txt

# 5. Execute a API
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

> Se receber erro `error: externally-managed-environment`, é porque o Python do Homebrew é gerenciado externamente. A solução é **sempre usar um venv** (passos 3–4 acima).

### 1.3 Windows (PowerShell)

Abra o **PowerShell** (não precisa ser como administrador) e execute:

```powershell
# 1. Clone o repositório
git clone https://github.com/SEU_USUARIO/b3-quote-api.git
cd b3-quote-api

# 2. Crie o ambiente virtual
python -m venv venv

# 3. Ative o ambiente virtual
.\venv\Scripts\Activate.ps1

# Se aparecer erro de "execução de scripts desabilitada", rode antes:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# e tente ativar novamente

# 4. Instale as dependências
pip install -r requirements.txt

# 5. Execute a API
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

*Se preferir o Prompt de Comando (CMD), o passo 3 muda para:* `venv\Scripts\activate.bat`

### 1.4 Testando localmente

Com a API rodando, abra **outro terminal** e teste:

```bash
# Linux/macOS
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/quote/PETR4
```

```powershell
# Windows (PowerShell) — use curl.exe, pois "curl" puro é um alias do PowerShell
curl.exe http://localhost:8000/health
curl.exe http://localhost:8000/api/v1/quote/PETR4

# Alternativa nativa do PowerShell:
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/api/v1/quote/PETR4
```

Ou simplesmente abra o navegador em: <http://localhost:8000/docs>

Para parar a API: `Ctrl+C` no terminal onde ela está rodando.

### 1.4b Rodando em modo de depuração SSL (apenas local)

Se a sua máquina estiver atrás de um proxy corporativo que intercepta HTTPS, você pode precisar desabilitar a verificação SSL _apenas para testes locais_. Para isso criamos `main_dev.py` que desabilita a verificação SSL apenas para o processo local.

Use somente para depuração local — NÃO use em produção.

```bash
# ative o venv antes, se aplicável
source .venv/bin/activate
python main_dev.py
```

Isso executa a mesma API (`app` do `main.py`) com a verificação de certificado desativada só para o processo local.

### 1.5 Testando com Docker no Windows (opcional)

Se quiser testar a versão containerizada no seu PC antes do deploy:

1. Instale o **Docker Desktop**: <https://www.docker.com/products/docker-desktop/>
2. Durante a instalação, aceite a opção de usar o **WSL 2** (o instalador configura automaticamente; pode pedir para reiniciar o PC).
3. Abra o Docker Desktop e aguarde o status "Engine running".
4. No PowerShell, dentro da pasta do projeto:

```powershell
docker compose up -d --build   # constrói a imagem e sobe o container
docker ps                      # verifica se está "Up (healthy)"
curl.exe http://localhost:8000/health
docker compose down            # para e remove quando terminar
```

---

## ☁️ 2. Deploy no Servidor Remoto (Oracle Cloud)

### 2.1 Pré-requisitos na OCI

1. VM criada (shape gratuito `VM.Standard.E2.1.Micro` ou `VM.Standard.A1.Flex` funciona bem) com **Ubuntu 22.04/24.04**.
2. Chave SSH configurada. Conecte-se:

```bash
ssh -i ~/.ssh/sua_chave.pem ubuntu@IP_PUBLICO_DA_VM
```

### 2.2 Configuração do Firewall (obrigatório — 2 camadas)

Na OCI o tráfego passa por **duas camadas** de firewall: a **Security List** da VCN (nuvem) e o **iptables/ufw** dentro da VM. É preciso liberar a porta **8000** nas duas.

#### Camada 1 — Security List da OCI (Console Web)

1. Console OCI → **Networking → Virtual Cloud Networks**.
2. Clique na VCN da sua VM → **Security Lists** → selecione a security list da subnet.
3. Clique em **Add Ingress Rules** e preencha:

| Campo | Valor |
|---|---|
| Source Type | CIDR |
| Source CIDR | `0.0.0.0/0` |
| IP Protocol | TCP |
| Destination Port Range | `8000` |
| Description | B3 Quote API |

4. Salve. (Para expor na porta 80, repita com `80`.)

#### Camada 2 — Firewall interno da VM (iptables)

As imagens Ubuntu da OCI vêm com regras `iptables` restritivas por padrão:

```bash
# Libera a porta 8000 (insere ANTES da regra de REJECT padrão da OCI)
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT

# Persiste as regras entre reboots
sudo apt-get update && sudo apt-get install -y iptables-persistent
sudo netfilter-persistent save
```

Se preferir usar `ufw`:

```bash
sudo ufw allow 22/tcp
sudo ufw allow 8000/tcp
sudo ufw enable
sudo ufw status
```

> ⚠️ Se usar `ufw` em imagem Ubuntu da OCI, garanta que a porta 22 (SSH) esteja liberada **antes** de ativar, para não perder acesso à VM.

**Teste rápido** (depois do deploy): `curl http://IP_PUBLICO_DA_VM:8000/health`

---

### 2.3 Opção A — Deploy Direto (Git + venv + systemd)

#### Passo 1 — Instalar dependências do sistema

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip
```

#### Passo 2 — Clonar o repositório

```bash
cd /home/ubuntu
git clone https://github.com/SEU_USUARIO/b3-quote-api.git
cd b3-quote-api
```

#### Passo 3 — Criar o ambiente virtual e instalar dependências

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate
```

#### Passo 4 — Testar manualmente (opcional, mas recomendado)

```bash
./venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
# Em outro terminal: curl http://localhost:8000/health
# Pare com Ctrl+C
```

#### Passo 5 — Instalar o serviço systemd (execução 24/7)

```bash
sudo cp api.service /etc/systemd/system/api.service
sudo systemctl daemon-reload
sudo systemctl enable --now api      # habilita no boot + inicia agora
```

> 📝 Se o projeto **não** estiver em `/home/ubuntu/b3-quote-api`, edite os caminhos `WorkingDirectory` e `ExecStart` no `api.service` antes de copiar.

#### Passo 6 — Verificar o serviço

```bash
sudo systemctl status api            # deve mostrar "active (running)"
journalctl -u api -f                 # logs em tempo real
curl http://localhost:8000/health    # teste local na VM
```

O `Restart=always` no `api.service` garante que o processo será reiniciado automaticamente em caso de falha, e o `enable` garante a subida automática após reboot da VM — **100% de disponibilidade**.

**Comandos úteis:**

```bash
sudo systemctl restart api    # reiniciar
sudo systemctl stop api       # parar
git pull && sudo systemctl restart api   # atualizar versão
```

---

### 2.4 Opção B — Deploy via Docker + Docker Compose

#### Passo 1 — Instalar o Docker na VM (Ubuntu)

Conectado na VM via SSH, execute os comandos abaixo **na ordem**:

```bash
# 1.1 Atualiza os pacotes do sistema
sudo apt-get update && sudo apt-get upgrade -y

# 1.2 Instala o Docker pelo script oficial (instala Engine + Compose plugin)
curl -fsSL https://get.docker.com | sudo sh

# 1.3 Adiciona seu usuário ao grupo docker (para usar sem "sudo")
sudo usermod -aG docker $USER

# 1.4 Aplica o novo grupo na sessão atual
#     (alternativa: deslogar e logar de novo no SSH)
newgrp docker

# 1.5 Garante que o Docker suba automaticamente no boot da VM
sudo systemctl enable --now docker
```

**Verifique se a instalação funcionou:**

```bash
docker --version            # ex: Docker version 27.x.x
docker compose version      # ex: Docker Compose version v2.x.x
docker run --rm hello-world # deve imprimir "Hello from Docker!"
sudo systemctl status docker  # deve mostrar "active (running)"
```

> ⚠️ Se aparecer `permission denied while trying to connect to the Docker daemon socket`, o grupo ainda não foi aplicado — deslogue (`exit`) e conecte via SSH novamente.

#### Passo 2 — Clonar o repositório

```bash
cd /home/ubuntu
git clone https://github.com/SEU_USUARIO/b3-quote-api.git
cd b3-quote-api
```

#### Passo 3 — Subir com um único comando

```bash
docker compose up -d --build
```

O que esse comando faz: `--build` constrói a imagem a partir do `Dockerfile`, e `-d` (detached) roda o container em segundo plano — você pode fechar o SSH que a API continua rodando.

O `restart: always` no `docker-compose.yml` garante que o container reinicie automaticamente após crash **e** após reboot da VM (o daemon do Docker sobe no boot, pois foi habilitado com `systemctl enable` no Passo 1).

*Alternativa sem compose (docker puro):*

```bash
docker build -t b3-quote-api .
docker run -d --name b3-quote-api --restart always -p 8000:8000 b3-quote-api
```

#### Passo 4 — Verificar

```bash
docker ps                            # STATUS deve ser "Up ... (healthy)"
docker logs -f b3-quote-api          # logs em tempo real
curl http://localhost:8000/health
```

**Comandos úteis:**

```bash
docker compose restart               # reiniciar
docker compose down                  # parar e remover
git pull && docker compose up -d --build   # atualizar versão
## 🔐 O que é SSL e o que é uma CA? (explicação simples)

SSL é o mecanismo que protege a conexão entre o seu navegador ou código e um site/serviço na internet. Em linguagem simples: é como uma "capa de segurança" para os dados que trafegam.

A CA (Certificate Authority, ou Autoridade Certificadora) é a entidade que emite e valida esse "documento digital". É como uma empresa que confirma: "este site é realmente quem diz que é".

Quando o seu computador diz que um certificado é inválido, normalmente o problema é um destes casos:

- o site usa um certificado antigo ou mal configurado;
- a sua rede está interceptando o tráfego com um certificado da empresa e o seu computador não conhece essa autoridade;
- a máquina local está em um ambiente corporativo com política de segurança mais rígida.

Nas máquinas da OCI e em um servidor Ubuntu normal, isso quase nunca é um problema, porque o sistema já vem com as CAs públicas conhecidas instaladas.

O problema costuma aparecer mais em notebooks corporativos, porque a empresa pode ter um proxy ou uma política de segurança que substitui certificados HTTPS por certificados internos.

Em resumo: uma CA é um "emissor de identidade digital" para HTTPS. Quando seu computador não a reconhece, o Python ou o navegador bloqueia a conexão por segurança.

### Quando isso importa aqui?

- Em um notebook da empresa ou rede corporativa: pode acontecer.
- Em uma VM pública na Oracle Cloud: normalmente não precisa de configuração extra.
- Para desenvolvimento local, quando isso acontece, pode ser útil testar com `main_dev.py` — mas só para depuração local e não em produção.

---

## 🔁 O que foi ajustado no projeto

- `main.py` foi mantido em modo produção, sem bypass de SSL.
- `main_dev.py` foi criado como arquivo específico para testes locais, com verificação SSL desativada apenas para o processo local.
- `Dockerfile` foi ajustado para instalar `ca-certificates`, ajudando containers a confiar nas CAs públicas do ambiente.
- `deploy_vm.sh` foi adicionado para facilitar o deploy em VM Ubuntu.

### Como usar para depuração local (somente local)

```bash
# ative o venv antes, se aplicável
source .venv/bin/activate
python main_dev.py
```

Isso baixa a verificação de certificado só para esse processo local. Em produção, use o `main.py` normal e isso não deve ser ativado.

---

## ✅ Recomendações finais

1. Use `main.py` e `uvicorn main:app --host 0.0.0.0 --port 8000 --reload` para produção e deploy normal.
2. Use `main_dev.py` somente se o seu notebook estiver atrás de proxy corporativo e a rede estiver emitindo certificados internos.
3. Em uma VM Ubuntu da OCI, normalmente não é necessário mexer em CA, porque ela já entende as autoridades públicas. O problema real costuma ser a máquina local da empresa, não a VM.

---

## 🔍 Resumo prático

- Se estiver no notebook da empresa e o Yahoo estiver sendo interceptado: pode ser problema de CA local.
- Se estiver na VM Ubuntu na OCI: normalmente não precisa de nada.
- Em produção: nunca desative SSL. Use o fluxo normal e os certificados válidos.

Abra no navegador:

```
http://IP_PUBLICO_DA_VM:8000/docs
```

O FastAPI gera automaticamente a documentação interativa (OpenAPI). Nela você pode expandir `GET /api/v1/quote/{ticker}`, clicar em **Try it out**, digitar um ticker (ex: `PETR4`) e clicar em **Execute** para testar direto pelo navegador.

---

## 🔒 4. Observações e melhorias futuras

- **Porta 80:** para expor na porta 80 sem root, use um proxy reverso (Nginx/Caddy) na frente do Uvicorn, ou redirecione com `iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 8000`.
- **Atraso dos dados:** o Yahoo Finance fornece dados da B3 com atraso de ~15 minutos (padrão do mercado para fontes gratuitas).
- **Melhorias possíveis:** cache (Redis) para reduzir chamadas à fonte, rate limiting, HTTPS com Let's Encrypt, CI/CD com GitHub Actions.

## 📄 Licença

Projeto acadêmico — livre para uso educacional.
