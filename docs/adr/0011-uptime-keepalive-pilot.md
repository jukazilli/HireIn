# ADR-0011 — Uptime externo e keep-alive controlado no piloto

## Status

Accepted.

## Contexto

O backend do piloto do HireIn roda em uma instância Free do Render. Instâncias Free entram em idle após um período sem tráfego e precisam de cold start no próximo request.

O frontend já possui retry controlado para leituras, mas o cold start ainda degrada a experiência do primeiro acesso.

Monitoramento externo pode enviar requests periódicos para a API, detectando indisponibilidade e, enquanto o intervalo for menor que a janela de idle, mantendo a instância ativa.

Ao mesmo tempo, horas de instâncias Free são compartilhadas no workspace do Render. O workspace atual contém outros serviços Free, portanto manter o HireIn acordado 24x7 tem custo de oportunidade mesmo quando o preço em dinheiro é zero.

## Problema

Precisamos equilibrar:

- boa experiência no primeiro carregamento;
- monitoramento externo real;
- custo próximo de zero;
- isolamento entre liveness e dependências;
- não consumir silenciosamente toda a franquia Free do workspace;
- evitar transformar um workaround do piloto em arquitetura definitiva.

## Alternativas consideradas

### 1. Aceitar sleep e depender somente do retry

Vantagens:

- consumo mínimo de horas Free;
- nenhuma dependência externa adicional.

Desvantagens:

- primeiro carregamento pode continuar lento;
- não oferece monitoramento externo nem alertas.

### 2. Uptime monitor externo chamando `/health/live`

Vantagens:

- reduz ou elimina cold starts enquanto os checks chegam regularmente;
- oferece alerta de indisponibilidade;
- baixo volume de requests;
- não toca em dados pessoais ou banco.

Desvantagens:

- pode manter a instância Free ativa continuamente;
- consome a franquia compartilhada do workspace;
- cria dependência operacional de um monitor externo.

### 3. Migrar imediatamente para Render pago

Vantagens:

- compute always-on;
- remove a motivação de keep-alive artificial.

Desvantagens:

- adiciona custo recorrente antes de o piloto comprovar necessidade.

## Decisão

1. `/health/live` é a rota oficial de liveness e monitoramento externo do HireIn.
2. A rota deve permanecer independente de PostgreSQL, Match, perfil, vagas e outras dependências.
3. A resposta deve usar `Cache-Control: no-store, max-age=0`.
4. `/health/ready` continua reservado para readiness, incluindo verificação de banco.
5. O frontend mantém retry controlado para leituras; monitor externo não substitui resiliência do cliente.
6. UptimeRobot Free é a primeira opção operacional para o piloto, com checks HTTP a cada 5 minutos.
7. O keep-alive 24x7 só deve ser habilitado após confirmar o orçamento de horas Free do workspace ou reduzir serviços antigos que estejam consumindo a mesma franquia.
8. Nenhum serviço de outro projeto será suspenso automaticamente para liberar horas para o HireIn.
9. Ao entrar em beta público ou quando disponibilidade previsível virar requisito, substituir a motivação de keep-alive por compute always-on adequado; o monitor externo permanece apenas como observabilidade.

## Consequências positivas

- health contract explícito;
- possibilidade de eliminar a necessidade de F5 após idle;
- monitoramento real da API;
- nenhum acesso a dados pessoais pelo monitor;
- separação correta entre liveness e readiness;
- decisão de custo consciente.

## Trade-offs

- keep-alive consome horas mesmo sem usuário real;
- o monitor não garante disponibilidade se a franquia Free acabar;
- o piloto continua dependente das limitações do Free tier;
- pode haver necessidade futura de reconfigurar alertas/provedor.

## Gatilhos de revisão

Revisar este ADR quando ocorrer qualquer um destes eventos:

- início do beta multiusuário;
- mudança de limites ou política do Render Free;
- mudança relevante no plano gratuito do provedor de uptime;
- consumo de horas Free causando suspensão;
- contratação de compute always-on;
- adoção de SLO/SLA formal;
- mudança do backend para outro provedor.

## Documento operacional

Ver `docs/15-UPTIME-KEEPALIVE.md`.
