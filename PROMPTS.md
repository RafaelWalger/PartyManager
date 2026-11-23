# Registro de prompts de IA

Ferramenta usada: **Claude (Anthropic)**, no app claude.ai.
Os prompts abaixo foram escritos pelo grupo, na ordem em que foram usados. O código gerado foi revisado e testado pelo grupo antes de entrar no repositório.

| # | Data | Pedido (resumo fiel do prompt) | O que a IA entregou |
|---|------|--------------------------------|---------------------|
| 1 | 20/11/2026 | "De acordo com esse PDF faz uma tela de login, landing page, Cobrar saldo, Ver relatórios, Ponto de venda, faz com CSS. Antes de você fazer me diga qual linguagem vai usar." (anexo: *PartyManager – Interface e Banco de Dados*) | Proposta de HTML + CSS + JavaScript e, após aprovação, as 5 telas estáticas. |
| 2 | 20/11/2026 | Trocar o estilo das páginas para **minimalista**, seguindo uma imagem de exemplo de tela de login, e mudar a paleta de cores. | Mesmas telas com visual minimalista (fundo claro, azul). |
| 3 | 22/11/2026 | "Me explica cada arquivo." | Explicação de cada arquivo e de como as telas se ligam. |
| 4 | 23/11/2026 | Lista de requisitos para o site ficar pronto para o GitHub, seguindo o modelo de repositório do grupo; CSS **preto e roxo** com variações festivas, **presets de cores**, **modo claro e escuro**, estilo inspirado no **Liquid Glass** da Apple (sem deixar todo menu transparente); **banco de dados real** para login e senha, sem simulações; **Equipe e Organizador fundamentalmente diferentes**. | Checklist de publicação e esta versão do projeto. |
| 5 | 23/11/2026 | "Será possível usar Java no backend? Se possível Oracle como banco de dados." | Projeto refeito em **Java (Spring Boot) + Oracle**, com scripts SQL, diagrama, README e este registro. |
| 6 | 23/11/2026 | A página de erro (`error.html`) deve ser genérica; como rodar o site no PC. | Página de erro com resposta única, sem detalhes técnicos; guia de execução no README. |
| 7 | 23/11/2026 | Como o professor vai acessar sem fazer o passo a passo? Tem que haver alguma forma de rodar, mesmo que por localhost. | Avaliação de opções de hospedagem; escolha do grupo: **`docker compose up`**, que sobe o Oracle e o site com um comando. |
| 8 | 23/11/2026 | (Claude Code) "Leia o CLAUDE.md e o resumo da conversa. Este projeto nunca foi compilado. Rode `docker compose up --build`, corrija os erros e teste o fluxo completo com as contas de exemplo." Depois: "verifique o quão versátil será trocar o código para Python, Vercel e Supabase, para rodar de forma mais simples para a correção do professor". | Comparação entre Docker + Oracle e Python + Supabase + Vercel (o professor só abre um link, mas o banco deixa de ser Oracle). |
| 9 | 23/11/2026 | (Claude Code) "Sim, migrar." | Projeto refeito em **Python (Flask) + PostgreSQL (Supabase) + Vercel**, com o mesmo visual e as mesmas regras; scripts SQL convertidos para PostgreSQL; fluxo completo testado com as contas de exemplo; README com o passo a passo de publicação. |

## Como continuar este registro

Ao usar IA de novo, adicione uma linha na tabela com a data, o pedido e o que foi aproveitado.
