-- =====================================================================
-- PartyManager — Dados de EXEMPLO (opcional)
-- Serve para testar e apresentar o sistema sem cadastrar tudo na mão.
--
-- Organizador:  demo@partymanager.com.br  /  senha Demo1234
-- Equipe:       código do evento DEMO26
--               paula / paula123  (ponto de venda e caixa, fixa no Bar 1)
--               lucas / lucas123  (portaria e resumo)
-- Ingressos:    PM-DEMO0001, PM-DEMO0002, PM-DEMO0003
-- As senhas abaixo estão em BCrypt, igual o sistema grava.
--
-- O bloco DO $$ ... $$ é um pequeno programa em PL/pgSQL: ele guarda
-- os IDs gerados em variáveis para ligar as tabelas entre si.
-- =====================================================================

DO $$
DECLARE
    v_org     BIGINT;
    v_evento  BIGINT;
    v_bar1    BIGINT;
    v_vip     BIGINT;
    v_normal  BIGINT;
BEGIN
    INSERT INTO organizador (nome, cpf, email, senha_hash, plano)
    VALUES ('Organizador Demonstração', '52998224725', 'demo@partymanager.com.br',
            '$2a$10$pLYSKqTenx.OSNzlDShue.PhbQUieZFVNQYh6tPFXDD7jdAW/yK3W', 'profissional')
    RETURNING id INTO v_org;

    INSERT INTO evento (organizador_id, nome, data_hora, local_evento, classificacao, capacidade, codigo_acesso)
    VALUES (v_org, 'Festa de Verão', TIMESTAMP '2026-12-19 22:00:00',
            'Clube Náutico, Vitória - ES', '18 anos', 300, 'DEMO26')
    RETURNING id INTO v_evento;

    -- Pontos de venda
    INSERT INTO ponto_venda (evento_id, nome) VALUES (v_evento, 'Bar 1') RETURNING id INTO v_bar1;
    INSERT INTO ponto_venda (evento_id, nome) VALUES (v_evento, 'Bar 2');
    INSERT INTO ponto_venda (evento_id, nome) VALUES (v_evento, 'Loja');

    -- Produtos (preço em centavos)
    INSERT INTO produto (evento_id, nome, categoria, preco, estoque) VALUES
        (v_evento, 'Chopp 500ml',    'bebida', 1200, 300),
        (v_evento, 'Água',           'bebida',  800, 200),
        (v_evento, 'Refrigerante',   'bebida',  700, 150),
        (v_evento, 'Hambúrguer',     'comida', 2500,  60),
        (v_evento, 'Copo do evento', 'loja',   1500, 200),
        (v_evento, 'Camiseta',       'loja',   6000,  30);

    -- Lotes
    INSERT INTO lote (evento_id, nome, preco, quantidade) VALUES (v_evento, 'VIP', 5000, 40) RETURNING id INTO v_vip;
    INSERT INTO lote (evento_id, nome, preco, quantidade) VALUES (v_evento, 'Antecipado', 2000, 100);
    INSERT INTO lote (evento_id, nome, preco, quantidade) VALUES (v_evento, 'Normal', 3000, 160) RETURNING id INTO v_normal;

    -- Alguns ingressos
    INSERT INTO ingresso (evento_id, lote_id, nome_participante, qr_code, valor) VALUES
        (v_evento, v_vip,    'Maria Silva',  'PM-DEMO0001', 5000),
        (v_evento, v_normal, 'João Pereira', 'PM-DEMO0002', 3000),
        (v_evento, v_normal, 'Ana Lima',     'PM-DEMO0003', 3000);

    -- Equipe
    INSERT INTO funcionario (evento_id, ponto_id, nome, usuario, senha_hash, perm_pdv, perm_caixa)
    VALUES (v_evento, v_bar1, 'Paula Souza', 'paula',
            '$2a$10$JYp8a8xOwfERGNq3b4iD4OhYO.aXkqjuziq9JUb.B64NhkzFZVkuK', TRUE, TRUE);
    INSERT INTO funcionario (evento_id, nome, usuario, senha_hash, perm_escanear, perm_relatorios)
    VALUES (v_evento, 'Lucas Martins', 'lucas',
            '$2a$10$XhPGHo0.490O8crI5N9heOI7t2CXOXnFbLXtNTS7NXNpfXQBYmu26', TRUE, TRUE);
END $$;
