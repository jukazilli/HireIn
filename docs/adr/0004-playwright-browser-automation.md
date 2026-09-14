# ADR-0004 — Playwright para automação de navegador

- **Status:** Accepted
- **Data:** 2026-09-14
- **Escopo:** preenchimento assistido e futura automação de fluxos de candidatura

## Contexto

Parte do valor do HireIn depende de interagir com ATSs e formulários de candidatura que não oferecem integração oficial adequada.

O agente precisa:

- abrir páginas;
- navegar por múltiplas etapas;
- preencher inputs;
- selecionar opções;
- anexar arquivos;
- detectar mensagens de erro;
- interromper quando encontrar perguntas desconhecidas;
- permitir supervisão humana;
- registrar evidências do que fez.

## Alternativas consideradas

### Selenium

É maduro e amplamente utilizado, mas Playwright oferece uma API moderna, auto-waiting, bom suporte a contextos isolados e forte integração com fluxos contemporâneos de navegador.

### Puppeteer

Boa ferramenta, especialmente no ecossistema Node, mas o core do HireIn está em Python. Adotá-la criaria uma stack adicional ou exigiria separar precocemente o browser agent.

### Playwright Python

Vantagens:

- integração direta com o core Python;
- suporte a Chromium, Firefox e WebKit;
- modo headed para supervisão;
- contextos de browser;
- interceptação e inspeção de eventos;
- boa capacidade de testes e tracing;
- API adequada para adapters determinísticos por ATS.

## Decisão

Adotar **Playwright Python** para o browser agent.

A primeira implementação deve operar em modo supervisionado e visível.

O agente não deve ser construído como um LLM controlando livremente o browser. A preferência é:

```text
ATS identificado
      ↓
adapter determinístico
      ↓
campos conhecidos
      ↓
validação
      ↓
usuário revisa
      ↓
submit manual/confirmado
```

IA poderá auxiliar em interpretação de perguntas, mas não substituir o controle de fluxo quando uma regra determinística for possível.

## Segurança e limites

O HireIn não deve depender de:

- evasão de CAPTCHA;
- fingerprint spoofing;
- stealth plugins para burlar controles;
- rotação de proxies com objetivo de mascarar automação;
- submissões massivas destinadas a contornar limites da plataforma.

Quando um mecanismo exigir ação humana ou impedir automação, o agente deve parar e solicitar intervenção.

## Consequências positivas

- boa observabilidade durante o piloto;
- uma única linguagem com o core;
- adapters testáveis;
- possibilidade de screenshots/traces para debugging;
- automação progressiva.

## Trade-offs

- manutenção contínua dos adapters;
- mudanças de DOM podem quebrar fluxos;
- alguns ATSs podem restringir automação;
- sessões e credenciais exigem cuidado especial.

## Gatilhos de revisão

Revisar se:

- integrações oficiais substituírem browser automation;
- o browser agent precisar escalar de forma independente;
- outro runtime oferecer confiabilidade mensuravelmente superior;
- manutenção dos adapters se tornar economicamente inviável.

## Regra

API oficial ou integração suportada deve ter preferência quando oferecer funcionalidade equivalente e termos compatíveis.
