# PartyManager

Sistema de gerenciamento de eventos por assinatura para pequenos eventos, desenvolvido como trabalho do curso de Ciência da Computação da FAESA.

Integrantes: Bernardo Pinotti Calenzani Simões, Rafael Walger Tovar, Samuel Floriano, Gabriel Leal Hoffoman e Kauã de Freitas.

Site: https://party-manager-mauve.vercel.app

## Contas de teste

Organizador (em /entrar): `demo@partymanager.com.br`, senha `Demo1234`.

Equipe (em /equipe/entrar), código do evento `DEMO26`:
- `paula`, senha `paula123`: ponto de venda e caixa
- `lucas`, senha `lucas123`: portaria e resumo

Ingressos para testar a portaria: `PM-DEMO0001`, `PM-DEMO0002` e `PM-DEMO0003`.

Também é possível criar uma conta nova de organizador em /cadastro. Nenhum plano é cobrado.

## Funcionalidades

O sistema tem duas áreas, cada uma com seu próprio login.

O organizador cria a conta, escolhe um plano e cadastra seus eventos. Para cada evento ele cria lotes de ingresso, emite ingressos com QR Code, cadastra produtos e pontos de venda, cria os acessos da equipe com as permissões de cada pessoa e acompanha vendas, entradas e saldo das pulseiras no painel. Compras feitas com a pulseira podem ser estornadas.

A equipe não tem cadastro. Cada funcionário entra com o código do evento, o usuário e a senha criados pelo organizador e só vê as funções liberadas para ele: portaria (validação de ingressos), ponto de venda, caixa (recarga e consulta de pulseiras) e resumo das vendas.

O pagamento das recargas é feito fora do sistema (maquininha, Pix ou dinheiro). O sistema registra a forma de pagamento e controla o saldo das pulseiras. A integração com um gateway de pagamento (RF03) não foi feita.

## Tecnologias

- Python 3.12 com Flask e Jinja2
- PostgreSQL no Supabase, acessado com SQL puro pela biblioteca psycopg
- Hospedagem no Vercel
- bcrypt para as senhas e qrcode para os ingressos
- HTML, CSS e JavaScript sem frameworks

## Estrutura

```
api/index.py      entrada do site no Vercel
app/
  rotas/          páginas do site (público, organizador e equipe)
  servicos/       regras de negócio
  dao/            consultas SQL
  templates/      HTML
  banco.py        conexão com o banco
  seguranca.py    login, senhas e proteção CSRF
public/           CSS, JavaScript, fontes e imagens
database/         scripts SQL (tabelas e dados de teste)
diagrams/         modelo relacional
executar.py       roda o site no computador
```

## Banco de dados

Os scripts ficam em `database/`:

1. `01_criacao_tabelas.sql` cria as tabelas.
2. `02_dados_exemplo.sql` cria as contas de teste.
3. `00_apagar_tabelas.sql` apaga tudo, para recomeçar do zero.

Para rodar, abra o projeto no Supabase, vá em SQL Editor e execute o conteúdo de cada arquivo.

O diagrama do modelo relacional está em `diagrams/modelo-relacional.md`.

## Rodar no computador

É preciso ter o Python 3.12 ou mais novo.

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Copie o arquivo `.env.example` para `.env` e preencha `DATABASE_URL` com o endereço do banco e `SECRET_KEY` com um texto aleatório. Depois execute:

```
python executar.py
```

O site abre em http://localhost:8080.

## Publicação

O site está no Vercel, ligado a este repositório: cada alteração enviada para a branch `main` é publicada automaticamente. O banco foi criado pela integração do Supabase dentro do Vercel, que já cadastra as variáveis de conexão no projeto.

O plano gratuito do Supabase pausa o banco depois de 7 dias sem acesso. Se isso acontecer, é só reativar o projeto no painel do Supabase.

## Segurança

- Senhas guardadas com bcrypt.
- Todos os formulários usam token CSRF.
- As consultas usam parâmetros, o que evita SQL Injection.
- O preço cobrado sempre vem do banco, e o saldo da pulseira nunca fica negativo.
- Venda, recarga e estorno são feitos em transação: se um passo falhar, nada é gravado.

## Uso de IA

Parte do código foi feita com ajuda de IA e revisada pelo grupo. Os prompts usados estão em [PROMPTS.md](PROMPTS.md).
