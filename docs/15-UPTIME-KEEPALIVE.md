# HireIn — Uptime, Cold Start e Keep-Alive do Piloto

> **Status:** estratégia operacional do piloto privado  
> **Data de referência:** 16/09/2026  
> **Objetivo:** reduzir cold starts do backend sem transformar o piloto em uma infraestrutura cara ou frágil

---

## 1. Contexto atual

O piloto privado do HireIn está hospedado com:

- frontend SvelteKit na Vercel;
- API FastAPI no Render;
- API em instância Free;
- PostgreSQL acessado pela API;
- frontend protegido por login do piloto;
- endpoints `/api/v1/*` protegidos por credencial server-to-server;
- health endpoints públicos e sem dados pessoais.

A instância Free do Render entra em idle depois de um período sem tráfego HTTP. O próximo request faz a instância voltar a subir, gerando cold start.

O frontend já possui retry controlado para operações de leitura quando a API está acordando. Esse mecanismo continua sendo obrigatório mesmo com monitor externo.

---

## 2. Contrato oficial de health

### `GET /health/live`

Uso:

- liveness;
- monitoramento externo;
- keep-alive do piloto quando explicitamente habilitado;
- health check leve.

Contrato:

```json
{"status":"ok"}
```

Requisitos arquiteturais:

- não consulta banco;
- não consulta Match;
- não lê perfil;
- não lê vagas;
- não exige token do piloto;
- não executa escrita;
- deve responder rapidamente enquanto o processo FastAPI estiver vivo;
- resposta usa `Cache-Control: no-store, max-age=0` para evitar que uma camada intermediária satisfaça o monitor sem alcançar a aplicação.

URL atual do piloto:

```text
https://hirein-api.onrender.com/health/live
```

### `GET /health/ready`

Uso:

- diagnóstico de prontidão;
- verificação de conexão com PostgreSQL;
- smoke tests e diagnóstico operacional.

Não deve ser usado como keep-alive frequente porque envolve dependência de banco e cria tráfego desnecessário.

---

## 3. Estratégia em três modos

### Modo A — Econômico

```text
Render Free pode dormir
        ↓
primeiro acesso acorda a API
        ↓
frontend executa retry de leitura
        ↓
usuário recebe os dados
```

Usar quando:

- custo mínimo é prioridade;
- o piloto tolera o primeiro carregamento mais lento;
- orçamento de horas Free do workspace está apertado.

Esse é o fallback permanente.

### Modo B — Piloto sempre aquecido

```text
Uptime monitor externo
        │
        │ GET periódico
        ▼
/health/live
        │
        ▼
FastAPI permanece recebendo tráfego
```

Configuração recomendada enquanto a API estiver no Render Free:

```text
Provider recomendado: UptimeRobot Free
Monitor type: HTTP(s)
URL: https://hirein-api.onrender.com/health/live
Método: GET
Intervalo: 5 minutos
HTTP esperado: 200
Nome sugerido: HireIn API — Liveness
```

O monitor pode ser alterado para um Keyword Monitor se quisermos validar também a presença de `"status":"ok"` no corpo.

### Modo C — Produção / beta público

Quando disponibilidade consistente passar a ser requisito de produto:

- API deve usar compute always-on adequado;
- monitor externo continua existindo para detecção de indisponibilidade;
- o monitor deixa de ser um mecanismo de keep-alive;
- retry do cliente continua existindo para falhas transitórias;
- SLO/SLA passa a ser definido com base em necessidade real.

Não devemos depender de pings artificiais como estratégia definitiva de produção.

---

## 4. Gate de custo antes de ativar keep-alive 24x7

O Render atualmente concede uma franquia mensal de horas de instâncias Free por workspace. Essa franquia é compartilhada entre serviços Free do mesmo workspace.

Em 16/09/2026, o workspace que hospeda o HireIn possui outros web services Free além de `hirein-api`, alguns não suspensos.

Consequência:

> manter `hirein-api` continuamente acordado pode consumir praticamente toda a franquia mensal disponível e reduzir a margem dos outros serviços.

Portanto, o monitor 24x7 só deve ser ativado depois de uma destas decisões:

1. confirmar que os outros serviços Free ativos podem continuar dormindo e o consumo agregado cabe na franquia;
2. suspender manualmente serviços antigos que não sejam mais necessários;
3. mover projetos antigos para outro workspace/infraestrutura quando fizer sentido;
4. aceitar a migração do HireIn para compute pago always-on quando disponibilidade justificar o custo.

O HireIn não deve suspender ou excluir recursos de outros projetos automaticamente.

---

## 5. Por que não usar `/health/ready` para keep-alive

`/health/ready` valida a dependência de banco.

Usá-lo a cada poucos minutos faria o monitor:

- abrir conexão com PostgreSQL repetidamente;
- transformar uma verificação de processo em verificação de dependência;
- aumentar ruído em logs;
- aumentar consumo desnecessário do banco;
- misturar liveness com readiness.

O padrão correto permanece:

```text
/health/live  → processo FastAPI está vivo
/health/ready → API + banco estão prontos
```

---

## 6. Alertas

O monitor externo deve tratar como incidente:

- timeout;
- erro de conexão;
- HTTP fora de 2xx;
- opcionalmente ausência de `"status":"ok"`.

Para o piloto, alertas por e-mail são suficientes.

Evitar integrações pagas de incident management antes de existir necessidade operacional real.

---

## 7. Retry continua obrigatório

O monitor externo não substitui o retry implementado no frontend.

Falhas ainda podem ocorrer por:

- deploy;
- troca de instância;
- manutenção do provedor;
- problema de rede;
- monitor atrasado ou indisponível;
- consumo da franquia Free;
- interrupção manual.

Por isso:

- GET/HEAD podem usar retry controlado;
- gravações não devem ser repetidas automaticamente sem idempotência explícita.

---

## 8. Critérios para abandonar o keep-alive Free

Migrar para compute always-on quando pelo menos uma destas condições for verdadeira:

- primeiro acesso precisa responder de forma previsível para usuários externos;
- beta multiusuário começou;
- cold start afeta testes, demos ou conversão;
- franquia Free do workspace se tornou fonte de indisponibilidade;
- monitor/keep-alive passou a exigir manutenção recorrente;
- custo de operação manual supera o preço do compute pago;
- SLA/SLO passa a ser requisito.

---

## 9. Referências operacionais

Revalidar antes de decisões futuras, porque limites e preços mudam:

- Render Free instances: https://render.com/docs/faq
- Render uptime best practices: https://render.com/docs/uptime-best-practices
- Render health checks: https://render.com/docs/health-checks
- UptimeRobot monitoring interval: https://help.uptimerobot.com/en/articles/11360876-what-is-a-monitoring-interval-in-uptimerobot
- UptimeRobot pricing: https://uptimerobot.com/pricing/
- UptimeRobot quick monitor setup for AI agents: https://uptimerobot.com/quick-monitor-setup/

---

## 10. Decisão operacional atual

- `/health/live` é a rota oficial de liveness e monitoramento externo do HireIn;
- `/health/ready` permanece para prontidão e diagnóstico do banco;
- retry de cold start permanece ativo no frontend;
- UptimeRobot Free é o provedor preferencial inicial para o piloto;
- keep-alive 24x7 deve respeitar o gate de horas Free compartilhadas do workspace;
- nenhum outro serviço Render será suspenso automaticamente para abrir espaço ao HireIn.
