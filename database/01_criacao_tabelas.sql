-- =====================================================================
-- PartyManager — Criação das tabelas (PostgreSQL 15+ / Supabase)
--
-- Como rodar no Supabase: abra o projeto > SQL Editor > New query,
-- cole este arquivo inteiro e clique em "Run". Depois faça o mesmo
-- com o 02_dados_exemplo.sql.
--
-- Valores em dinheiro ficam em CENTAVOS (BIGINT) para não ter erro de
-- arredondamento. Ex.: R$ 12,50 = 1250.
-- Os IDs são gerados pelo próprio banco (GENERATED ALWAYS AS IDENTITY,
-- que é uma sequence automática) e devolvidos com INSERT ... RETURNING id.
-- =====================================================================

-- ---------------------------------------------------------------------
-- ORGANIZADOR: quem contrata o plano e cria eventos
-- ---------------------------------------------------------------------
CREATE TABLE organizador (
    id                 BIGINT        GENERATED ALWAYS AS IDENTITY CONSTRAINT pk_organizador PRIMARY KEY,
    nome               VARCHAR(120)  NOT NULL,
    cpf                VARCHAR(11)   NOT NULL CONSTRAINT uq_organizador_cpf UNIQUE,
    email              VARCHAR(160)  NOT NULL CONSTRAINT uq_organizador_email UNIQUE,
    senha_hash         VARCHAR(100)  NOT NULL,
    plano              VARCHAR(20)   NOT NULL DEFAULT 'basico'
                       CONSTRAINT ck_organizador_plano
                       CHECK (plano IN ('basico', 'profissional', 'festival')),
    status_assinatura  VARCHAR(20)   NOT NULL DEFAULT 'ativa'
                       CONSTRAINT ck_organizador_status
                       CHECK (status_assinatura IN ('ativa', 'pendente', 'cancelada')),
    tema               VARCHAR(20)   NOT NULL DEFAULT 'neon',
    modo               VARCHAR(10)   NOT NULL DEFAULT 'escuro'
                       CONSTRAINT ck_organizador_modo CHECK (modo IN ('escuro', 'claro')),
    criado_em          TIMESTAMPTZ   NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- EVENTO
-- data_hora é o horário "de parede" do evento (sem fuso), como foi digitado.
-- ---------------------------------------------------------------------
CREATE TABLE evento (
    id              BIGINT        GENERATED ALWAYS AS IDENTITY CONSTRAINT pk_evento PRIMARY KEY,
    organizador_id  BIGINT        NOT NULL
                    CONSTRAINT fk_evento_organizador REFERENCES organizador (id) ON DELETE CASCADE,
    nome            VARCHAR(120)  NOT NULL,
    data_hora       TIMESTAMP     NOT NULL,
    local_evento    VARCHAR(200)  NOT NULL,
    classificacao   VARCHAR(20)   NOT NULL DEFAULT 'Livre',
    capacidade      INTEGER       NOT NULL CONSTRAINT ck_evento_capacidade CHECK (capacidade > 0),
    codigo_acesso   VARCHAR(10)   NOT NULL CONSTRAINT uq_evento_codigo UNIQUE,
    criado_em       TIMESTAMPTZ   NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- LOTE de ingressos (VIP, Antecipado, Normal...)
-- ---------------------------------------------------------------------
CREATE TABLE lote (
    id          BIGINT       GENERATED ALWAYS AS IDENTITY CONSTRAINT pk_lote PRIMARY KEY,
    evento_id   BIGINT       NOT NULL
                CONSTRAINT fk_lote_evento REFERENCES evento (id) ON DELETE CASCADE,
    nome        VARCHAR(60)  NOT NULL,
    preco       BIGINT       NOT NULL CONSTRAINT ck_lote_preco CHECK (preco >= 0),
    quantidade  INTEGER      NOT NULL CONSTRAINT ck_lote_quantidade CHECK (quantidade > 0)
);

-- ---------------------------------------------------------------------
-- INGRESSO: cada um tem um código único que vira QR Code
-- ---------------------------------------------------------------------
CREATE TABLE ingresso (
    id                  BIGINT        GENERATED ALWAYS AS IDENTITY CONSTRAINT pk_ingresso PRIMARY KEY,
    evento_id           BIGINT        NOT NULL
                        CONSTRAINT fk_ingresso_evento REFERENCES evento (id) ON DELETE CASCADE,
    lote_id             BIGINT        NOT NULL
                        CONSTRAINT fk_ingresso_lote REFERENCES lote (id) ON DELETE CASCADE,
    nome_participante   VARCHAR(120)  NOT NULL,
    email_participante  VARCHAR(160),
    qr_code             VARCHAR(20)   NOT NULL CONSTRAINT uq_ingresso_qr UNIQUE,
    valor               BIGINT        NOT NULL,
    status              VARCHAR(12)   NOT NULL DEFAULT 'valido'
                        CONSTRAINT ck_ingresso_status CHECK (status IN ('valido', 'usado', 'cancelado')),
    usado_em            TIMESTAMPTZ,
    criado_em           TIMESTAMPTZ   NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- PONTO DE VENDA: Bar 1, Bar 2, Loja, Food truck...
-- ---------------------------------------------------------------------
CREATE TABLE ponto_venda (
    id          BIGINT       GENERATED ALWAYS AS IDENTITY CONSTRAINT pk_ponto_venda PRIMARY KEY,
    evento_id   BIGINT       NOT NULL
                CONSTRAINT fk_ponto_evento REFERENCES evento (id) ON DELETE CASCADE,
    nome        VARCHAR(60)  NOT NULL
);

-- ---------------------------------------------------------------------
-- PRODUTO vendido no evento
-- ---------------------------------------------------------------------
CREATE TABLE produto (
    id          BIGINT       GENERATED ALWAYS AS IDENTITY CONSTRAINT pk_produto PRIMARY KEY,
    evento_id   BIGINT       NOT NULL
                CONSTRAINT fk_produto_evento REFERENCES evento (id) ON DELETE CASCADE,
    nome        VARCHAR(80)  NOT NULL,
    categoria   VARCHAR(10)  NOT NULL DEFAULT 'bebida'
                CONSTRAINT ck_produto_categoria CHECK (categoria IN ('bebida', 'comida', 'loja')),
    preco       BIGINT       NOT NULL CONSTRAINT ck_produto_preco CHECK (preco > 0),
    estoque     INTEGER      NOT NULL CONSTRAINT ck_produto_estoque CHECK (estoque >= 0),
    ativo       BOOLEAN      NOT NULL DEFAULT TRUE
);

-- ---------------------------------------------------------------------
-- FUNCIONARIO: membro da equipe. Só existe dentro de um evento e entra
-- com código do evento + usuário + senha (não tem cadastro próprio).
-- ---------------------------------------------------------------------
CREATE TABLE funcionario (
    id               BIGINT        GENERATED ALWAYS AS IDENTITY CONSTRAINT pk_funcionario PRIMARY KEY,
    evento_id        BIGINT        NOT NULL
                     CONSTRAINT fk_funcionario_evento REFERENCES evento (id) ON DELETE CASCADE,
    ponto_id         BIGINT
                     CONSTRAINT fk_funcionario_ponto REFERENCES ponto_venda (id) ON DELETE SET NULL,
    nome             VARCHAR(120)  NOT NULL,
    usuario          VARCHAR(40)   NOT NULL,
    senha_hash       VARCHAR(100)  NOT NULL,
    perm_escanear    BOOLEAN       NOT NULL DEFAULT FALSE,
    perm_pdv         BOOLEAN       NOT NULL DEFAULT FALSE,
    perm_caixa       BOOLEAN       NOT NULL DEFAULT FALSE,
    perm_relatorios  BOOLEAN       NOT NULL DEFAULT FALSE,
    ativo            BOOLEAN       NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_funcionario_usuario UNIQUE (evento_id, usuario)
);

-- ---------------------------------------------------------------------
-- CARTAO_SALDO: pulseira / cartão NFC com saldo
-- O CHECK garante no banco que o saldo nunca fica negativo.
-- ---------------------------------------------------------------------
CREATE TABLE cartao_saldo (
    id          BIGINT       GENERATED ALWAYS AS IDENTITY CONSTRAINT pk_cartao_saldo PRIMARY KEY,
    evento_id   BIGINT       NOT NULL
                CONSTRAINT fk_cartao_evento REFERENCES evento (id) ON DELETE CASCADE,
    uid_nfc     VARCHAR(40)  NOT NULL,
    saldo       BIGINT       NOT NULL DEFAULT 0 CONSTRAINT ck_cartao_saldo CHECK (saldo >= 0),
    ativo       BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_cartao_uid UNIQUE (evento_id, uid_nfc)
);

-- ---------------------------------------------------------------------
-- TRANSACAO: toda movimentação de saldo (débito, recarga ou estorno)
-- ---------------------------------------------------------------------
CREATE TABLE transacao (
    id                   BIGINT       GENERATED ALWAYS AS IDENTITY CONSTRAINT pk_transacao PRIMARY KEY,
    cartao_id            BIGINT       NOT NULL
                         CONSTRAINT fk_transacao_cartao REFERENCES cartao_saldo (id) ON DELETE CASCADE,
    funcionario_id       BIGINT
                         CONSTRAINT fk_transacao_funcionario REFERENCES funcionario (id) ON DELETE SET NULL,
    ponto_id             BIGINT
                         CONSTRAINT fk_transacao_ponto REFERENCES ponto_venda (id) ON DELETE SET NULL,
    valor                BIGINT       NOT NULL CONSTRAINT ck_transacao_valor CHECK (valor > 0),
    tipo                 VARCHAR(10)  NOT NULL
                         CONSTRAINT ck_transacao_tipo CHECK (tipo IN ('debito', 'recarga', 'estorno')),
    forma_pagamento      VARCHAR(10)
                         CONSTRAINT ck_transacao_forma CHECK (forma_pagamento IN ('pix', 'cartao', 'dinheiro')),
    transacao_origem_id  BIGINT
                         CONSTRAINT fk_transacao_origem REFERENCES transacao (id),
    criado_em            TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- ---------------------------------------------------------------------
-- ITEM_TRANSACAO: produtos de uma compra (estoque e relatórios)
-- ---------------------------------------------------------------------
CREATE TABLE item_transacao (
    id              BIGINT   GENERATED ALWAYS AS IDENTITY CONSTRAINT pk_item_transacao PRIMARY KEY,
    transacao_id    BIGINT   NOT NULL
                    CONSTRAINT fk_item_transacao REFERENCES transacao (id) ON DELETE CASCADE,
    produto_id      BIGINT   NOT NULL
                    CONSTRAINT fk_item_produto REFERENCES produto (id) ON DELETE CASCADE,
    quantidade      INTEGER  NOT NULL CONSTRAINT ck_item_quantidade CHECK (quantidade > 0),
    preco_unitario  BIGINT   NOT NULL
);

-- ---------------------------------------------------------------------
-- ÍNDICES para as consultas mais usadas
-- ---------------------------------------------------------------------
CREATE INDEX idx_evento_organizador ON evento (organizador_id);
CREATE INDEX idx_ingresso_evento    ON ingresso (evento_id);
CREATE INDEX idx_produto_evento     ON produto (evento_id);
CREATE INDEX idx_transacao_cartao   ON transacao (cartao_id);
CREATE INDEX idx_transacao_ponto    ON transacao (ponto_id);
CREATE INDEX idx_item_transacao     ON item_transacao (transacao_id);

-- Uma compra só pode ser estornada UMA vez (o banco garante, mesmo com dois cliques ao mesmo tempo)
CREATE UNIQUE INDEX uq_transacao_estorno ON transacao (transacao_origem_id)
    WHERE transacao_origem_id IS NOT NULL;

-- ---------------------------------------------------------------------
-- SEGURANÇA NO SUPABASE
-- O Supabase publica automaticamente uma API REST para as tabelas do
-- schema "public". Ligando o RLS (Row Level Security) sem criar nenhuma
-- regra, essa API não enxerga nada. O site não é afetado, porque ele
-- conecta direto no banco com o usuário dono das tabelas.
-- (Num PostgreSQL comum, fora do Supabase, estes comandos não atrapalham.)
-- ---------------------------------------------------------------------
ALTER TABLE organizador    ENABLE ROW LEVEL SECURITY;
ALTER TABLE evento         ENABLE ROW LEVEL SECURITY;
ALTER TABLE lote           ENABLE ROW LEVEL SECURITY;
ALTER TABLE ingresso       ENABLE ROW LEVEL SECURITY;
ALTER TABLE ponto_venda    ENABLE ROW LEVEL SECURITY;
ALTER TABLE produto        ENABLE ROW LEVEL SECURITY;
ALTER TABLE funcionario    ENABLE ROW LEVEL SECURITY;
ALTER TABLE cartao_saldo   ENABLE ROW LEVEL SECURITY;
ALTER TABLE transacao      ENABLE ROW LEVEL SECURITY;
ALTER TABLE item_transacao ENABLE ROW LEVEL SECURITY;
