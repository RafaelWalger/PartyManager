-- =====================================================================
-- PartyManager — Apaga TODAS as tabelas do projeto.
-- Use só quando quiser recomeçar do zero (os dados serão perdidos!).
-- Depois rode o 01_criacao_tabelas.sql e o 02_dados_exemplo.sql de novo.
-- =====================================================================

DROP TABLE IF EXISTS item_transacao, transacao, cartao_saldo, funcionario, produto,
                     ponto_venda, ingresso, lote, evento, organizador CASCADE;
