# PartyManager

Sistema de gerenciamento de eventos por assinatura para pequenos eventos.
**Crie, gerencie, venda e controle seu evento em um só lugar.**

Projeto acadêmico do curso de Ciência da Computação (FAESA).

**Integrantes:** Bernardo Pinotti Calenzani Simões, Rafael Walger Tovar, Samuel Floriano, Gabriel Leal Hoffoman e Kauã de Freitas.

> **Site no ar:** https://party-manager-mauve.vercel.app
>
> Não precisa instalar nada: é só abrir o link e entrar com as contas de teste abaixo.

| Área | Onde | Dados |
|---|---|---|
| Organizador | `/entrar` | `demo@partymanager.com.br` / `Demo1234` |
| Equipe (PDV e caixa) | `/equipe/entrar` | código `DEMO26`, usuário `paula`, senha `paula123` |
| Equipe (portaria e resumo) | `/equipe/entrar` | código `DEMO26`, usuário `lucas`, senha `lucas123` |

Ingressos de teste para a portaria: `PM-DEMO0001`, `PM-DEMO0002`, `PM-DEMO0003`.

---

## O que o sistema faz

O PartyManager tem **duas áreas separadas**, com login, layout e funções diferentes:

| | Organizador | Equipe (funcionário) |
|---|---|---|
| **Como entra** | Cria a própria conta (e-mail + senha) em `/cadastro` | Não tem cadastro. Entra em `/equipe/entrar` com **código do evento + usuário + senha** criados pelo organizador |
| **Tela** | Painel de gestão com menu lateral | "Modo operador": tela cheia, botões grandes, pensado para o celular |
| **Funções** | Eventos, lotes e ingressos com QR Code, produtos e pontos de venda, pulseiras NFC, transações e estornos, equipe e permissões, painel ao vivo, aparência | Só o que o organizador liberou: **Portaria** (valida QR Code e lista de acesso), **Ponto de venda** (vende e cobra na pulseira), **Caixa** (recarrega e consulta pulseiras), **Resumo** (entradas e vendas da pessoa) |

### Requisitos atendidos (do documento do projeto)

| Requisito | Onde está |
|---|---|
| RF01 Contratar plano de assinatura | Cadastro com escolha de plano; limites aplicados em `app/modelos.py` |
| RF02 Cadastrar evento com dados completos | `/organizador/eventos` |
| RF03 Pagar via Pix, cartão, boleto ou gateway | Forma de pagamento registrada na recarga. **Integração com gateway: pendente** |
| RF04 Criar lotes de ingressos com QR Code | `/organizador/ingressos` (QR gerado com a biblioteca `qrcode`) |
| RF05 Vender produtos na loja do evento | Equipe → Ponto de venda |
| RF06 Recarregar, cobrar e estornar saldo NFC | Equipe → Caixa e Ponto de venda; Organizador → Transações (estorno) |
| RF07 Validar ingressos pelo app (scanner) | Equipe → Portaria (leitor USB, câmera ou digitação) |
| RF08 Gerenciar equipe e permissões | `/organizador/equipe` |
| RF09 Ver relatórios de vendas e saldo | `/organizador` (painel ao vivo) e Equipe → Resumo |
| RNF01 Segurança | Senhas com BCrypt, proteção CSRF, sessão em cookie assinado |
| RNF02 Antifraude | QR Code de uso único, saldo nunca negativo (regra no banco), preço sempre vindo do banco |
| RNF05 Dados em tempo real | Painel atualiza a cada 30 segundos |
| RNF06 Web + leitura NFC e QR | Web NFC e câmera no Chrome/Android (o site no Vercel já é HTTPS) |
| RNF07 Interface em português | Todo o sistema |

## Tecnologias

- **Python 3.12** + **Flask** (site e rotas) e **Jinja2** (páginas HTML)
- **PostgreSQL** no **Supabase** (banco na nuvem, plano grátis), com **SQL puro** pelo driver `psycopg`
- **Vercel** (hospedagem grátis com HTTPS)
- **bcrypt** para as senhas e **qrcode** para o QR Code dos ingressos
- **CSS próprio** (sem framework), estilo inspirado no Liquid Glass, com 5 temas de cor e modo claro/escuro
- **JavaScript puro** só onde precisa (carrinho, leitura de QR/NFC, troca de tema)
- Fontes **Bricolage Grotesque** e **Figtree** hospedadas no próprio projeto (licença OFL)

## Estrutura do repositório

```
PartyManager/
├── api/
│   └── index.py              # entrada do site no Vercel
├── app/
│   ├── __init__.py           # monta o site: configuração, rotas e tratamento de erros
│   ├── banco.py              # conexão com o PostgreSQL e funções de SQL
│   ├── seguranca.py          # login das duas áreas, senhas (BCrypt) e CSRF
│   ├── modelos.py            # planos, temas e erros do sistema
│   ├── formatador.py         # R$, datas e números no padrão brasileiro
│   ├── utilidades.py         # CPF, dinheiro, código da pulseira...
│   ├── icones.py             # ícones SVG
│   ├── dao/                  # SQL puro, um arquivo por tabela/área
│   ├── servicos/             # regras de negócio (venda, recarga, estorno...)
│   ├── rotas/                # páginas: publico.py, organizador.py, equipe.py
│   └── templates/            # páginas HTML (publico/, organizador/, equipe/)
├── public/                   # css/, js/, fonts/, img/ (servidos direto pelo Vercel)
├── database/
│   ├── 00_apagar_tabelas.sql # apaga tudo (para recomeçar)
│   ├── 01_criacao_tabelas.sql
│   └── 02_dados_exemplo.sql  # contas e dados de teste
├── diagrams/                 # modelo relacional (Mermaid; o GitHub desenha)
├── executar.py               # roda o site no seu PC
├── requirements.txt          # bibliotecas Python
├── vercel.json               # manda as páginas para o api/index.py
├── .env.example
├── .gitignore
├── PROMPTS.md                # registro dos prompts de IA usados
└── README.md
```

## Como o código está organizado

Uma requisição passa por três camadas, sempre na mesma ordem:

1. **Rota** (`app/rotas/`): recebe o formulário, chama o serviço e escolhe a página.
2. **Serviço** (`app/servicos/`): aplica as regras (ex.: "saldo insuficiente", "lote esgotado").
3. **DAO** (`app/dao/`): roda o SQL no banco.

Erros "esperados" são lançados como `RegraNegocio("mensagem")` e viram um aviso na tela.
Operações com vários passos (venda, recarga, estorno) rodam dentro de `with banco.transacao():`:
se qualquer passo falhar, o banco desfaz tudo.

---

## Publicar o site (feito uma vez pelo grupo)

O banco é criado **de dentro do Vercel** (integração com o Supabase). Assim o Vercel já cadastra
sozinho o endereço e a senha do banco nas variáveis do site, e ninguém precisa copiar senha.

1. Suba o projeto para o GitHub (confira que o `.env` **não** foi junto).
2. Crie uma conta grátis em [vercel.com](https://vercel.com) entrando com o GitHub.
3. **Add New → Project** → escolha o repositório → em **Framework Preset** deixe **Other** → **Deploy**.
   (Este primeiro deploy ainda mostra erro, porque o banco não existe. É normal.)
4. No projeto do Vercel, abra **Storage → Create Database → Supabase**, escolha a região
   **São Paulo** e o plano grátis, e conecte ao projeto. O Vercel cria as variáveis `POSTGRES_URL`,
   `POSTGRES_PASSWORD` e outras; o site lê essas variáveis sozinho (`app/banco.py` e `app/__init__.py`).
5. Ainda em **Storage**, clique em **Open in Supabase** → **SQL Editor** → **New query**. Cole todo o
   `database/01_criacao_tabelas.sql` e clique em **Run**. Depois faça o mesmo com o `database/02_dados_exemplo.sql`.
6. Em **Deployments**, abra o último deploy → **⋯ → Redeploy** (para o site enxergar as variáveis novas).
7. Abra `https://<nome>.vercel.app/saude`: se aparecer **ok**, o site está falando com o banco.
   Coloque o link no topo deste README.

O site roda na região de São Paulo (`"regions": ["gru1"]` no `vercel.json`), perto do banco.
A cada `git push`, o Vercel publica a nova versão sozinho.

> **Sem a integração** (banco criado direto em supabase.com): cadastre no Vercel as variáveis
> `DATABASE_URL` (URI do **Transaction pooler**, porta 6543, com `?sslmode=require` no final) e
> `SECRET_KEY` (gere com `python -c "import secrets; print(secrets.token_hex(32))"`).

### Antes de mandar o link ao professor

O plano grátis do Supabase **pausa o projeto depois de 7 dias sem nenhum acesso**. Abra o site
(ou o `/saude`) de vez em quando, principalmente nos dias antes e durante a correção. Se pausar,
entre no painel do Supabase e clique em **Restore project** (leva poucos minutos; os dados continuam lá).

---

## Rodar no seu PC (para desenvolver)

1. Instale o **[Python 3.12 ou mais novo](https://www.python.org/downloads/)** (marque *Add python.exe to PATH*).
2. Na pasta do projeto, crie o ambiente e instale as bibliotecas:

   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

   (Linux/macOS: `source .venv/bin/activate` no lugar da segunda linha.)

3. Copie o `.env.example` para `.env` e preencha `DATABASE_URL` (pode ser o mesmo banco do Supabase) e `SECRET_KEY`.
4. Rode:

   ```powershell
   python executar.py
   ```

   e abra **http://localhost:8080**. Para recarregar sozinho ao salvar arquivos, coloque `DEBUG=1` no `.env`.

### Problemas comuns

| Mensagem | O que fazer |
|---|---|
| `Configure SECRET_KEY e DATABASE_URL` | O `.env` não existe ou está incompleto (precisa estar na pasta do projeto) |
| `/saude` mostra **banco indisponível** | Confira a `DATABASE_URL` (senha, porta 6543, `?sslmode=require`) ou se o projeto do Supabase está pausado |
| `password authentication failed` | Senha do banco errada na `DATABASE_URL` |
| `relation "organizador" does not exist` | Faltou rodar o `01_criacao_tabelas.sql` no SQL Editor do Supabase |
| `prepared statement ... already exists` | Use a URI do **Transaction pooler** (porta 6543), como no passo 1.4 |
| `Address already in use` | Troque `PORTA=8081` no `.env` |

## Leitura de QR Code e NFC

- **Leitor USB ou Bluetooth** (de QR ou de NFC): funciona em qualquer navegador. Ele "digita" o código no campo e aperta Enter.
- **Câmera do celular** para QR Code: aparece o botão "Usar câmera" no Chrome (Android e desktop).
- **NFC do celular**: aparece o botão "Ler com o celular" no Chrome para Android.
- Câmera e NFC só funcionam com o site em **HTTPS** (o link do Vercel já é) ou em `localhost`.

## Segurança

- Senhas guardadas com **BCrypt** (nunca em texto puro).
- Todo formulário POST tem **token CSRF** (`{{ m.csrf() }}` nos templates); sem ele o pedido é recusado.
- Quem está logado fica num **cookie assinado** com a `SECRET_KEY` (não dá para alterar sem a chave).
- Os logins do organizador e da equipe são **separados** (`app/seguranca.py`).
- O funcionário desativado pelo organizador **perde o acesso na hora**, mesmo já logado.
- O valor cobrado é calculado com os **preços do banco**, nunca com o que veio da tela.
- Venda, recarga e estorno rodam em **transação**: se algo falhar no meio, o banco desfaz tudo.
- Todo SQL usa parâmetros (`%s`), o que impede **SQL Injection**.
- As tabelas têm **RLS** ligado no Supabase, então a API pública do Supabase não enxerga nenhum dado.
- Senhas e chaves ficam no `.env` (no PC) e nas variáveis do Vercel, fora do repositório.

## Aparência

Cinco temas (Roxo neon, Réveillon, Carnaval, Pôr do sol e Aurora), cada um com modo claro e escuro.
O organizador salva a escolha na conta (`Conta e aparência`); a equipe e os visitantes usam o botão de lua/sol e a escolha fica salva no navegador.
As cores ficam em `public/css/temas.css`: para criar um tema novo, copie um bloco e troque as cores.

## Uso de IA

Partes do código foram geradas com ajuda de IA e revisadas pelo grupo. Os prompts estão em [PROMPTS.md](PROMPTS.md).
